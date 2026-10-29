#!/usr/bin/python3
import argparse
import sys
from wsled_client import WSLEDClient

def main():
    parser = argparse.ArgumentParser(description="WS281x Userland CLI (wsled-ctl)")
    parser.add_argument("color", type=str, nargs='?', help="Color name, #rgb or #rrggbb")
    parser.add_argument("-i", "--index", type=int, help="Specific pixel index")
    parser.add_argument("-b", "--brightness", type=float, default=1.0, 
                        help="Intensity multiplier, clamped to 0.0-1.0. Default: 1.0")
    parser.add_argument("-p", "--poll", action="store_true", help="Poll pixel count")
    
    args = parser.parse_args()
    client = WSLEDClient()

    if args.poll:
        count = client.get_count()
        if count:
            print(f"Connected Pixels: {count}")
        else:
            print("Error: Could not connect to LED Proxy.")
            sys.exit(1)
        return

    if args.color:
        # Use the intensity-aware method
        try:
            ok = client.set_intensity_color(args.color, intensity=args.brightness, index=args.index)
        except ValueError as e:
            parser.error(str(e))
        if not ok:
            print("Error: Could not connect to LED Proxy.")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
