import pkgutil
from typing import List


def list_ops_modules() -> List[str]:
    import pist01beat.ops as ops_pkg

    names = []
    for m in pkgutil.iter_modules(ops_pkg.__path__):
        if m.name.startswith("_"):
            continue
        names.append(m.name)
    return sorted(names)


def main() -> None:
    for name in list_ops_modules():
        print(name)


if __name__ == "__main__":
    main()
