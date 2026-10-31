"""Offline preparation only: no USB, socket, queue, daemon, or discovery code.

Windows evidence fixes the canvas and job parameters; Pillow rendering is a
portable implementation, not a byte-identical ImageMagick reproduction.
"""
from dataclasses import dataclass
from io import BytesIO
import os
import struct
from PIL import Image, ImageOps, ImageCms

CANVAS = (1216, 1824)
TARGET_BYTES = 512 * 1024

# 实测相纸规格(media-size) -> 像素画布 @300dpi (米家桌面照片打印机2, ZMRSHZP02HT)


class Unsupported(ValueError):
    pass


@dataclass(frozen=True)
class PreparedImage:
    jpeg: bytes
    quality: int
    size: tuple[int, int] = CANVAS


def load_jpeg_pil(data: bytes) -> "Image.Image":
    """Decode JPEG with EXIF orientation and ICC->sRGB flattening; shared by"""
    if len(data) > 32 * 1024 * 1024:
        raise Unsupported("image exceeds offline input limit")
    try:
        src = Image.open(BytesIO(data))
    except OSError as exc:
        raise Unsupported("input is not a supported JPEG") from exc
    with src:
        if src.format != "JPEG":
            raise Unsupported("only JPEG input is implemented; PDF/URF/PWG need renderers")
        if src.width * src.height > 40_000_000:
            raise Unsupported("image exceeds pixel limit")
        image = ImageOps.exif_transpose(src).convert("RGB")
        if src.info.get("icc_profile"):
            try:
                image = ImageCms.profileToProfile(
                    image, ImageCms.ImageCmsProfile(BytesIO(src.info["icc_profile"])),
                    ImageCms.createProfile("sRGB"), outputMode="RGB")
            except (OSError, ValueError, ImageCms.PyCMSError) as exc:
                raise Unsupported("invalid or unsupported embedded ICC profile") from exc
    return image


def prepare_jpeg(data: bytes, *, scaling="fill", rotate_180=False, centering=(0.5,0.5), orientation=None) -> PreparedImage:
    """EXIF orient, fit/fill portrait canvas, flatten white, JPEG quality 60..100."""
    if scaling not in ("fill", "fit"):
        raise Unsupported("only fill and fit are implemented")
    image = load_jpeg_pil(data)
    return prepare_rgb(image.tobytes(), image.width, image.height,
                       scaling=scaling, rotate_180=rotate_180, centering=centering, orientation=orientation)


def best_photo_orientation(width,height):
    """Choose 0/90 degrees by retained area under center-fill; ties stay natural."""
    ratio=width/height;target=CANVAS[0]/CANVAS[1]
    normal=min(ratio/target,target/ratio)
    turned=min((1/ratio)/target,target/(1/ratio))
    return 4 if turned>normal+1e-12 else 3


def prepare_rgb(pixels: bytes, width: int, height: int, *, scaling="fill", rotate_180=False, centering=(0.5,0.5), orientation=None):
    if scaling not in ("fill", "fit"):
        raise Unsupported("only fill and fit are implemented")
    if width < 1 or height < 1 or width*height > 40_000_000 or len(pixels) != width*height*3:
        raise Unsupported("invalid sRGB pixel buffer")
    if len(centering)!=2 or any(not 0<=v<=1 for v in centering):
        raise Unsupported("crop center must be within 0..1")
    image = Image.frombytes("RGB", (width, height), pixels)
    if orientation not in (None,3,4,5,6):raise Unsupported("unsupported explicit orientation")
    canvas=CANVAS
    landscape=orientation in (4,5) or orientation is None and best_photo_orientation(width,height)==4
    if landscape:canvas=CANVAS[::-1]
    if scaling == "fill":
        image = ImageOps.fit(image, canvas, Image.Resampling.LANCZOS, centering=centering)
    else:
        inner = ImageOps.contain(image, canvas, Image.Resampling.LANCZOS)
        image = Image.new("RGB", canvas, "white")
        image.paste(inner, ((canvas[0]-inner.width)//2, (canvas[1]-inner.height)//2))
    if landscape:image=image.transpose(Image.Transpose.ROTATE_90)
    if rotate_180 or orientation in (5,6):
        image = image.transpose(Image.Transpose.ROTATE_180)

    def encode(q):
        buf = BytesIO()
        srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        image.save(buf, "JPEG", quality=q, progressive=False, optimize=True, icc_profile=srgb)
        return buf.getvalue()

    top = encode(100)
    if len(top) <= TARGET_BYTES:
        return PreparedImage(top, 100, CANVAS)
    best = encode(60)
    if len(best) > TARGET_BYTES:
        raise Unsupported("JPEG exceeds 512 KiB even at quality 60; refusing silent quality loss")
    quality, lo, hi = 60, 61, 99
    while lo <= hi:
        mid = (lo + hi)//2
        candidate = encode(mid)
        if len(candidate) <= TARGET_BYTES:
            quality, best, lo = mid, candidate, mid+1
        else:
            hi = mid-1
    return PreparedImage(best, quality, CANVAS)


def rotate180_pi(image: PreparedImage) -> PreparedImage:
    """方形背胶相纸(5009): 固件在画布顶部留物理白边, 旋转180°使其落在照片底部"""
    with Image.open(BytesIO(image.jpeg)) as src:
        im = src.convert("RGB").rotate(180)
        out = BytesIO()
        im.save(out, "JPEG", quality=95, subsampling=0)
        return PreparedImage(out.getvalue(), 95, image.size)


SPLICE_HALF = (CANVAS[0], CANVAS[1] // 2)   # 5014 每半 1216x912 (横版 4:3)


def compose_splice(images, *, scaling="fill") -> PreparedImage:
    """5014 拼接版(可撕成上下两张)排版: 整版仍是 1216x1824, 上下两半(各1216x912)"""
    if scaling not in ("fill", "fit"):
        raise Unsupported("only fill and fit are implemented")
    if not images:
        raise Unsupported("splice needs at least one image")
    hw, hh = SPLICE_HALF
    halves = []
    for im in images[:2]:
        im = im.convert("RGB")
        if scaling == "fill":
            halves.append(ImageOps.fit(im, (hw, hh), Image.Resampling.LANCZOS))
        else:
            inner = ImageOps.contain(im, (hw, hh), Image.Resampling.LANCZOS)
            frame = Image.new("RGB", (hw, hh), "white")
            frame.paste(inner, ((hw - inner.width) // 2, (hh - inner.height) // 2))
            halves.append(frame)
    if len(halves) == 1:
        halves = halves * 2
    canvas = Image.new("RGB", CANVAS, "white")
    canvas.paste(halves[0], (0, 0))
    canvas.paste(halves[1], (0, hh))
    out = BytesIO()
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    canvas.save(out, "JPEG", quality=95, subsampling=0, icc_profile=srgb)
    return PreparedImage(out.getvalue(), 95, CANVAS)


# IPP subset for offline binary fixtures. No network transport is implemented.
@dataclass(frozen=True)
class Attribute:
    group: int
    tag: int
    name: str
    value: bytes


@dataclass(frozen=True)
class Message:
    version: tuple[int, int]
    code: int
    request_id: int
    attributes: tuple[Attribute, ...]
    document: bytes = b""

    def values(self, name):
        return [a.value for a in self.attributes if a.name == name]


def decode_ipp(raw: bytes) -> Message:
    if len(raw) < 9:
        raise Unsupported("truncated IPP header")
    major, minor, code, rid = struct.unpack_from(">BBHI", raw)
    if (major, minor) not in [(1, 1), (2, 0)]:
        raise Unsupported("IPP version outside implemented subset")
    pos, group, previous, attrs = 8, None, None, []
    def take(n):
        nonlocal pos
        if pos+n > len(raw):
            raise Unsupported("truncated IPP attribute")
        result = raw[pos:pos+n]
        pos += n
        return result
    def collection(depth=0):
        if depth > 4:
            raise Unsupported("collection nesting limit")
        start, have_member = pos, False
        while True:
            nested_tag = take(1)[0]
            name_len = struct.unpack(">H", take(2))[0]
            if name_len:
                raise Unsupported("collection member has nonzero name-length")
            length = struct.unpack(">H", take(2))[0]
            value = take(length)
            if nested_tag == 0x37:
                if length:
                    raise Unsupported("invalid endCollection")
                return raw[start:pos]
            if nested_tag == 0x4a:
                if not value:
                    raise Unsupported("empty collection member name")
                have_member = True
            elif not have_member or nested_tag < 0x10:
                raise Unsupported("invalid collection member")
            elif nested_tag == 0x34:
                if length:
                    raise Unsupported("invalid beginCollection")
                collection(depth+1)
    while pos < len(raw):
        tag = take(1)[0]
        if tag == 3:
            return Message((major, minor), code, rid, tuple(attrs), raw[pos:])
        if tag <= 15:
            if tag not in (1, 2, 4, 5):
                raise Unsupported("unsupported delimiter group")
            group, previous = tag, None
            continue
        if group is None or tag in (0x37, 0x4a):
            raise Unsupported("missing group or unimplemented collection syntax")
        name = take(struct.unpack(">H", take(2))[0])
        value = take(struct.unpack(">H", take(2))[0])
        if name:
            try:
                previous = name.decode("ascii")
            except UnicodeDecodeError as exc:
                raise Unsupported("invalid attribute name") from exc
        elif previous is None:
            raise Unsupported("continuation without attribute name")
        if tag == 0x34:
            if value:
                raise Unsupported("invalid collection value-length")
            value = collection()
        attrs.append(Attribute(group, tag, previous, value))
    raise Unsupported("missing end-of-attributes")


def encode_ipp(message: Message) -> bytes:
    out = bytearray(struct.pack(">BBHI", *message.version, message.code, message.request_id))
    group, previous = None, None
    for a in message.attributes:
        if a.tag==0:
            out.append(a.group);group,previous=a.group,None;continue
        if a.group != group:
            out.append(a.group)
            group, previous = a.group, None
        name = b"" if a.name == previous else a.name.encode("ascii")
        out.extend(struct.pack(">BH", a.tag, len(name))+name)
        out.extend(struct.pack(">H", 0 if a.tag == 0x34 else len(a.value))+a.value)
        previous = a.name
    return bytes(out)+b"\x03"+message.document


def collection_values(data):
    """Decode validated collection bytes into named (tag, value) pairs."""
    pos, member, result = 0, None, {}
    def parse():
        nonlocal pos
        values, name = {}, None
        while True:
            tag, name_len = struct.unpack_from(">BH", data, pos); pos += 3
            if name_len: raise Unsupported("invalid collection")
            length = struct.unpack_from(">H", data, pos)[0]; pos += 2
            value = data[pos:pos+length]; pos += length
            if tag == 0x37: return values
            if tag == 0x4a:
                name = value.decode("ascii")
            else:
                if name is None or name in values: raise Unsupported("ambiguous collection")
                values[name] = (tag, parse() if tag == 0x34 else value)
    try:
        result = parse()
    except (struct.error, UnicodeDecodeError, IndexError) as exc:
        raise Unsupported("invalid collection") from exc
    if pos != len(data): raise Unsupported("trailing collection bytes")
    return result


def encode_collection(values):
    out = bytearray()
    for name, (tag, value) in values.items():
        name = name.encode("ascii")
        out.extend(struct.pack(">BHH", 0x4a, 0, len(name))+name)
        value = encode_collection(value) if tag == 0x34 else value
        out.extend(struct.pack(">BHH", tag, 0, 0 if tag == 0x34 else len(value))+value)
    return bytes(out)+b"\x37\x00\x00\x00\x00"
