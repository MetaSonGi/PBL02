# caesar_decode.py
from pathlib import Path

def _shift_char(ch: str, k: int) -> str:
    if 'A' <= ch <= 'Z':
        base = ord('A')
        return chr((ord(ch) - base - k) % 26 + base)
    if 'a' <= ch <= 'z':
        base = ord('a')
        return chr((ord(ch) - base - k) % 26 + base)
    return ch

def _decode_with_shift(text: str, k: int) -> str:
    return ''.join(_shift_char(c, k) for c in text)

def caesar_cipher_decode(target_text: str):
    print("=== 카이사르 해독 후보 (0~25) ===")
    candidates = {}
    for k in range(26):
        decoded = _decode_with_shift(target_text, k)
        candidates[k] = decoded
        print(f"[{k:02}] {decoded}")

    sel = input("\n정답으로 보이는 시프트 번호(0~25)를 입력하고 Enter (건너뛰려면 그냥 Enter): ").strip()
    if sel == "":
        print("저장 생략: 아무 것도 입력하지 않았습니다.")
        return

    try:
        idx = int(sel)
        if not (0 <= idx <= 25):
            raise ValueError
    except ValueError:
        print("유효하지 않은 입력입니다. 0~25 사이 정수를 입력하세요.")
        return

    out_path = Path("result.txt")
    with out_path.open("w", encoding="utf-8") as f:
        f.write(candidates[idx])
    print(f"저장 완료: {out_path.resolve()} (시프트 {idx})")

if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    pw_path = base / "password.txt"

    if not pw_path.exists():
        print(f"password.txt 를 찾지 못했습니다: {pw_path}")
        print("같은 폴더에 password.txt를 두거나, 직접 문자열을 넣어 caesar_cipher_decode()를 호출하세요.")
    else:
        text = pw_path.read_text(encoding="utf-8", errors="ignore")
        caesar_cipher_decode(text)
