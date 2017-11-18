import argparse
import os

parser = argparse.ArgumentParser(description='market analyzer for input currency pairs (tsym, fsym)')

#parser.add_argument('count', action="store", type=int)
parser.add_argument('tsym', action="store")
parser.add_argument('fsym', action="store")
parser.add_argument('upload', action="store", type=str)

args = parser.parse_args()

print(args.tsym)
print(args.fsym)
if(args.upload):
    print("uploaded")

print(os.getcwd())