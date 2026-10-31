"""AirPrint capabilities and request validation."""
import struct,time
from .offline import Attribute as A,collection_values,encode_collection
from .documents import FORMATS
URF=(b'V1.4',b'CP1',b'RS300',b'SRGB24',b'W8')
OPS=(2,4,5,6,8,9,10,11)
def integer(value):return struct.pack('>i',value)
class IppFailure(Exception):
    def __init__(self,status,message):self.status,self.message=status,message
class Capabilities:
    @property
    def media_name(self):return b'custom_square_3x3in' if self.media==5009 else b'na_index-4x6_4x6in'
    @property
    def paper_mm(self):return (7620,7620) if self.media==5009 else (10160,15240)
    def printer_attributes(self):
        accepting = not self.core.paused and (self.core.simulate or self.core.device.get('connected',False))
        attrs = [A(4,0x42,"printer-name","小米照片打印机 2".encode("utf-8")),
            A(4,0x41,"printer-info","小米照片打印机 2".encode("utf-8")),
            A(4,0x45,"printer-uri-supported",self.uri.encode()),
            A(4,0x45,"printer-uuid",self.identity.encode()),
            A(4,0x44,"uri-security-supported",b"none"),
            A(4,0x44,"uri-authentication-supported",b"none"),
            A(4,0x22,"printer-is-accepting-jobs",bytes([bool(accepting)])),
            A(4,0x23,"printer-state",integer(3 if accepting else 5)),
            A(4,0x41,"printer-state-message",('Ready' if accepting else 'Printer unavailable; checking connection').encode()[:512]),
            A(4,0x44,"printer-state-reasons",b"none" if accepting else b"paused"),
            A(4,0x42,"printer-make-and-model",b"Mijia Instant Photo Printer 2 (experimental bridge)"),
            A(4,0x47,"charset-configured",b"utf-8"),
            A(4,0x47,"charset-supported",b"utf-8"),
            A(4,0x48,"natural-language-configured",b"en"),
            A(4,0x48,"generated-natural-language-supported",b"en"),
            A(4,0x49,"document-format-default",b"image/jpeg"),
            A(4,0x44,"media-default",self.media_name), A(4,0x44,"media-supported",self.media_name), A(4,0x44,"media-ready",self.media_name),
            A(4,0x22,"color-supported",b"\x01"),
            A(4,0x44,"print-color-mode-supported",b"color"),
            A(4,0x44,"print-color-mode-default",b"color"),
            A(4,0x44,"sides-supported",b"one-sided"), A(4,0x44,"sides-default",b"one-sided"),
            A(4,0x21,"copies-default",integer(1)), A(4,0x33,"copies-supported",integer(1)+integer(1)),
            A(4,0x22,"multiple-document-jobs-supported",b"\0"),
            A(4,0x23,"orientation-requested-default",integer(3)),
            *[A(4,0x23,"orientation-requested-supported",integer(x)) for x in (3,4,5,6)],
            A(4,0x21,"queued-job-count",integer(sum(j['phase']=='queued' for j in self.core.jobs))),
            A(4,0x33,"job-k-octets-supported",integer(1)+integer(32768)),
            A(4,0x44,"compression-supported",b"none"),
            *[A(4,0x44,"media-col-supported",x) for x in (b"media-size",b"media-type",b"media-left-margin",b"media-right-margin",b"media-top-margin",b"media-bottom-margin")],
            A(4,0x44,"media-type-default",b"photographic"),A(4,0x44,"media-type-supported",b"photographic"),
            *[A(4,0x44,n,b"center") for n in ("x-image-position-default","x-image-position-supported","y-image-position-default","y-image-position-supported")],
            A(4,0x22,"job-ids-supported",b"\x01"),
            A(4,0x21,"printer-up-time",integer(int(time.monotonic()-self.started))),
            A(4,0x44,"print-scaling-default",b"fill"),
            A(4,0x44,"print-scaling-supported",b"fit"), A(4,0x44,"print-scaling-supported",b"fill"),

            A(4,0x23,"print-quality-default",integer(5)), A(4,0x23,"print-quality-supported",integer(5)),
            # 300dpi describes accepted client raster rendering, not device DPI.
            A(4,0x32,"printer-resolution-default",integer(300)+integer(300)+b"\x03"),
            A(4,0x32,"printer-resolution-supported",integer(300)+integer(300)+b"\x03"),
            A(4,0x32,"pwg-raster-document-resolution-supported",integer(300)+integer(300)+b"\x03"),
            A(4,0x44,"pwg-raster-document-type-supported",b"srgb_8"),
            A(4,0x44,"pwg-raster-document-type-supported",b"sgray_8")]
        attrs += [A(4,0x49,"document-format-supported",v.encode()) for v in FORMATS]
        attrs += [A(4,0x23,"operations-supported",integer(v)) for v in OPS]
        attrs += [A(4,0x44,"ipp-versions-supported",v) for v in (b"1.1",b"2.0")]
        attrs += [A(4,0x44,"urf-supported",v) for v in URF]
        size = {"media-size": (0x34,{"x-dimension":(0x21,integer(self.paper_mm[0])),"y-dimension":(0x21,integer(self.paper_mm[1]))})}
        size["media-type"]=(0x44,b"photographic")
        size.update({k:(0x21,integer(0)) for k in ('media-left-margin','media-right-margin','media-top-margin','media-bottom-margin')})
        attrs.extend(A(4,0x21,k,integer(0)) for k in ('media-left-margin-supported','media-right-margin-supported','media-top-margin-supported','media-bottom-margin-supported'))
        attrs.append(A(4,0x34,"media-col-default",encode_collection(size)))
        attrs.append(A(4,0x34,"media-col-database",encode_collection(size)))
        if not self.core.simulate and not self.core.device.get('connected'):
            attrs=[a for a in attrs if a.name!='media-ready']
        return attrs

    def _one(self, req, name, default=None):
        values = req.values(name)
        if len(values)>1: raise IppFailure(0x0400,"duplicate "+name)
        return values[0] if values else default

    def _validate(self, req):
        mime = self._one(req,"document-format",b"image/jpeg").decode("ascii")
        if mime not in FORMATS: raise IppFailure(0x040a,"document format not implemented")
        if self._one(req,"media",self.media_name) != self.media_name: raise IppFailure(0x040b,"requested paper does not match service paper")
        if self._one(req,"copies",integer(1)) != integer(1): raise IppFailure(0x040b,"one copy per AirPrint job")
        if self._one(req,"sides",b"one-sided") != b"one-sided": raise IppFailure(0x040b,"one-sided only")
        if self._one(req,"compression",b"none") != b"none": raise IppFailure(0x040b,"compression not implemented")
        orientation=self._one(req,"orientation-requested",integer(3))
        if orientation not in tuple(integer(x) for x in (3,4,5,6)):
            raise IppFailure(0x040b,"unsupported orientation")
        if self._one(req,"print-quality",integer(5)) not in (integer(4),integer(5)):raise IppFailure(0x040b,"unsupported quality; high quality is default")
        if self._one(req,"printer-resolution",integer(300)+integer(300)+b"\x03") != integer(300)+integer(300)+b"\x03":raise IppFailure(0x040b,"300 dpi client raster only")
        if self._one(req,"number-up",integer(1)) != integer(1): raise IppFailure(0x040b,"number-up not implemented")
        if self._one(req,"job-hold-until",b"no-hold") != b"no-hold": raise IppFailure(0x040b,"job holding not implemented")
        if self._one(req,"print-color-mode",b"color") != b"color": raise IppFailure(0x040b,"color profile only")
        scaling = self._one(req,"print-scaling",b"fill").decode("ascii")
        if scaling not in ("fit","fill"): raise IppFailure(0x040b,"only implemented fit/fill scaling supported")
        for name in ('x-image-position','y-image-position'):
            if self._one(req,name,b'center')!=b'center':raise IppFailure(0x040b,'only centered placement implemented')
        if self._one(req,'media-type',b'photographic')!=b'photographic':raise IppFailure(0x040b,'photographic paper only')
        media_col = self._one(req,"media-col")
        if media_col is not None:
            col = collection_values(media_col)
            if set(col)-{"media-size","media-type","media-left-margin","media-right-margin","media-top-margin","media-bottom-margin"}:
                raise IppFailure(0x040b,"unsupported media collection member")
            if col.get('media-type',(0x44,b'photographic'))!=(0x44,b'photographic'):raise IppFailure(0x040b,'photographic paper only')
            size = col.get("media-size")
            if size != (0x34,{"x-dimension":(0x21,integer(self.paper_mm[0])),"y-dimension":(0x21,integer(self.paper_mm[1]))}):
                raise IppFailure(0x040b,"requested paper size does not match service paper")
            for name,(tag,val) in col.items():
                if name.endswith("margin") and (tag != 0x21 or val != integer(0)):
                    raise IppFailure(0x040b,"nonzero requested margins not implemented")
        return mime, scaling, orientation in (integer(5),integer(6))
