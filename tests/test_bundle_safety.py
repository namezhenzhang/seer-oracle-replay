import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from seer_replay.download import unpack


class BundleSafety(unittest.TestCase):
    def test_rejects_escape_and_links(self):
        for name, kind in [
            ("../outside", tarfile.REGTYPE),
            ("/absolute", tarfile.REGTYPE),
            ("link", tarfile.SYMTYPE),
        ]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                bundle = root / "x.tar.gz"
                out = root / "out"
                out.mkdir()
                with tarfile.open(bundle, "w:gz") as t:
                    m = tarfile.TarInfo(name)
                    m.type = kind
                    m.linkname = "../outside"
                    m.size = 0
                    t.addfile(m, io.BytesIO(b""))
                with self.assertRaises(RuntimeError):
                    unpack(bundle, out, 10)
                self.assertFalse((root / "outside").exists())

    def test_size_bound_and_valid_member(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            bundle = root / "x.tar.gz"
            out = root / "out"
            out.mkdir()
            with tarfile.open(bundle, "w:gz") as t:
                m = tarfile.TarInfo("replay/value.txt")
                m.size = 3
                t.addfile(m, io.BytesIO(b"abc"))
            with self.assertRaises(RuntimeError):
                unpack(bundle, out, 2)
            self.assertEqual(unpack(bundle, out, 3), 1)
            self.assertEqual((out / "replay/value.txt").read_bytes(), b"abc")


if __name__ == "__main__":
    unittest.main()
