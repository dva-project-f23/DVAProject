import subprocess
import sys


def generate_prisma_client():
    """Generates the Prisma Client and loads it"""
    print(f"GENERATING PRISMA CLIENT")
    subprocess.call(["prisma", "generate"])
    print(f"GENERATED PRISMA CLIENT")


generate_prisma_client()

try:
    from generated.prisma import Prisma
except RuntimeError:
    from prisma_cleanup import cleanup

    cleanup()
    print("GOT RUNTIME ERROR")
    generate_prisma_client()
    from generated.prisma import Prisma
