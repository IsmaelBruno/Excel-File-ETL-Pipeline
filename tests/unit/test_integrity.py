from __future__ import annotations

from atg_excel_pipeline.integrity import sha256_file


def test_sha256_fichier_vide(tmp_path) -> None:
    path = tmp_path / "vide.bin"
    path.write_bytes(b"")
    assert sha256_file(path) == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_sha256_contenu_connu(tmp_path) -> None:
    path = tmp_path / "a.bin"
    path.write_bytes(b"abc")
    assert sha256_file(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
