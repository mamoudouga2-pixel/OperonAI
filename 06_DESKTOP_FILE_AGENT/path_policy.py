from pathlib import Path

from errors import E


class PathPolicy:
    """6.9 PATH POLICY.

    - allowed_roots: only paths inside one of these are ever usable.
    - restricted_roots: sensitive subtrees that are always denied, even if
      they sit underneath an allowed root.
    - symlinks are denied by default (policy-controlled via allow_symlinks).
    """

    def __init__(self, allowed_roots, restricted_roots=(), allow_overwrite=False,
                 delete_requires_approval=True, allow_symlinks=False):
        self.allowed = tuple(Path(x).resolve() for x in allowed_roots)
        self.restricted = tuple(Path(x).resolve() for x in restricted_roots)
        self.allow_overwrite = allow_overwrite
        self.delete_requires_approval = delete_requires_approval
        self.allow_symlinks = allow_symlinks

    def _under(self, p, roots):
        return any(p == r or r in p.parents for r in roots)

    def is_restricted(self, path):
        """True if `path` (resolved) falls inside a restricted root.

        Used by callers (e.g. the recursive scanner) to prune subtrees
        *before* descending into them, not just at the top-level call.
        """
        p = Path(path)
        if not p.is_absolute():
            p = Path.cwd() / p
        p = p.resolve(strict=False)
        return self._under(p, self.restricted)

    def validate(self, path, must_exist=False):
        p = Path(path)
        if not p.is_absolute():
            p = Path.cwd() / p
        if p.exists() and p.is_symlink() and not self.allow_symlinks:
            raise RuntimeError(E.PATH_NOT_ALLOWED)
        p = p.resolve(strict=False)
        if self._under(p, self.restricted):
            raise RuntimeError(E.PATH_NOT_ALLOWED)
        if not self._under(p, self.allowed):
            raise RuntimeError(E.PATH_NOT_ALLOWED)
        if must_exist and not p.exists():
            raise RuntimeError(E.FILE_NOT_FOUND)
        return p
