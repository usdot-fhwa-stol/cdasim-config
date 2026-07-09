import carla
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description='Set CARLA spectator view position, rotation, and server host.')
parser.add_argument('--host', type=str, default='localhost', help='Host address of the CARLA server (default: localhost)')
parser.add_argument('--x', type=float, default=0.0, help='X coordinate of spectator position (meters)')
parser.add_argument('--y', type=float, default=0.0, help='Y coordinate of spectator position (meters)')
parser.add_argument('--z', type=float, default=50.0, help='Z coordinate of spectator position (meters)')
parser.add_argument('--pitch', type=float, default=-90.0, help='Pitch angle of spectator rotation (degrees)')
parser.add_argument('--yaw', type=float, default=0.0, help='Yaw angle of spectator rotation (degrees)')
parser.add_argument('--roll', type=float, default=0.0, help='Roll angle of spectator rotation (degrees)')

# Parse arguments
args = parser.parse_args()

# Connect to CARLA server
client = carla.Client(args.host, 2000)
client.set_timeout(10.0)

# Get world and spectator
world = client.get_world()
spectator = world.get_spectator()

# Set spectator transform
spectator.set_transform(carla.Transform(
    carla.Location(x=args.x, y=args.y, z=args.z),
    carla.Rotation(pitch=args.pitch, yaw=args.yaw, roll=args.roll)
))

print(f"Connected to CARLA server at {args.host}:2000")
print(f"Spectator set to position (x={args.x}, y={args.y}, z={args.z}) and rotation (pitch={args.pitch}, yaw={args.yaw}, roll={args.roll})")