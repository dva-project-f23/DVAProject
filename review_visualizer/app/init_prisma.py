import subprocess
import sys


def generate_prisma_client():
    """Generates the Prisma Client and loads it"""
    print(f"GENERATING PRISMA CLIENT")
    subprocess.check_call(["prisma", "generate"], stdout=sys.stdout, stderr=sys.stderr)
    print(f"GENERATED PRISMA CLIENT")


generate_prisma_client()
try:
    from prisma import Prisma
except RuntimeError:
    from prisma_cleanup import cleanup

    cleanup()
    print(f"GOT RUNTIME ERROR")
    generate_prisma_client()
    from prisma import Prisma
