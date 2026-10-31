"""Windows Web and AirPrint service using the shared editor and print queue."""
import argparse
import asyncio
import hashlib
import ipaddress
import os
from pathlib import Path
import socket
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop.serve import run


def arguments(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--entry', choices=('web', 'airprint', 'both'), default='both')
    p.add_argument('--simulate', action='store_true')
    p.add_argument('--lan', action='store_true')
    p.add_argument('--announce', action='store_true')
    p.add_argument('--address', help='This PC IPv4 address on the shared network')
    p.add_argument('--allow-network', action='append', default=[])
    p.add_argument('--printer-name', default='Liuying Photo Printer')
    p.add_argument('--web-port', type=int, default=8635)
    p.add_argument('--ipp-port', type=int, default=8636)
    p.add_argument('--paper', choices=('auto', 'splice'), default='auto')
    folder = Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'AppData/Local')))/'MijiaPrintStudio'
    p.add_argument('--data', type=Path, default=folder)
    args = p.parse_args(argv)
    if any(not 1 <= port <= 65535 for port in (args.web_port, args.ipp_port)):
        p.error('Ports must be 1..65535')
    if args.entry == 'both' and args.web_port == args.ipp_port:
        p.error('Web and AirPrint need different ports')
    if not args.simulate and sys.platform != 'win32':
        p.error('Real Bluetooth transport requires native Windows Python')
    if not args.simulate and not os.environ.get('MIJIA_BLUETOOTH_ADDRESS'):
        p.error('Set MIJIA_BLUETOOTH_ADDRESS or use --simulate')
    try:
        networks = [ipaddress.ip_network(value, strict=False) for value in args.allow_network]
        if args.address:
            address = ipaddress.IPv4Address(args.address)
            if address.is_loopback or address.is_unspecified or address.is_multicast or address.is_link_local or not address.is_private:
                p.error('--address must be this PC private LAN IPv4 address')
    except ValueError:
        p.error('Invalid IPv4 address or trusted network')
    if args.lan and args.entry != 'web' and (not networks or not args.address):
        p.error('LAN AirPrint needs --address and --allow-network')
    if args.announce and (not args.lan or args.simulate or args.entry == 'web'):
        p.error('Discovery requires real LAN AirPrint')
    # A separate name for each PC/data directory prevents duplicate host records.
    identity = hashlib.sha256((socket.gethostname()+'|'+str(args.data.resolve())).encode()).hexdigest()[:12]
    args.hostname = 'liuying-'+identity+'.local' if args.announce else args.address or 'localhost'
    if args.address:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.bind((args.address, 0))
        except OSError:
            p.error('--address is not assigned to this PC')
    return args


def main():
    args = arguments()
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
