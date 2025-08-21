import cv2
import os
import sys
from pathlib import Path

# 허용 확장자
VALID_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def get_image_files(folder: Path):
    """폴더 및 하위 폴더에서 이미지 파일 목록 가져오기 (재귀)"""
    files = []
    for p in folder.rglob("*"):
        if p.is_file() and p.suffix.lower() in VALID_EXTS:
            files.append(p)
    files.sort(key=lambda x: x.as_posix().lower())
    return files

def detect_people(image):
    """사람 감지 후 박스 그려 반환"""
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    rects, _ = hog.detectMultiScale(image, winStride=(4, 4), padding=(8, 8), scale=1.05)
    for (x, y, w, h) in rects:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return len(rects) > 0, image


def main(target_folder: str = "."):
    # 스크립트 파일 기준으로 경로 해석 (작업 디렉토리와 무관하게 동작)
    base_dir = Path(__file__).resolve().parent
    folder = (base_dir / target_folder).resolve()

    if not folder.exists():
        print(f"'{folder}' 폴더를 찾을 수 없습니다.")
        sys.exit(1)

    images = get_image_files(folder)
    if not images:
        print(f"이미지 파일이 없습니다. 검색 위치: {folder}")
        sys.exit(1)

    print(f"{len(images)}개의 이미지를 검색합니다. (Enter를 누르면 다음 사진 진행, ESC 종료)")

    for idx, path in enumerate(images, 1):
        img = cv2.imread(str(path))
        if img is None:
            print(f"열 수 없는 파일 건너뜀: {path.name}")
            continue

        found, out = detect_people(img)
        if found:
            print(f"{idx}/{len(images)}: 사람 감지됨 → {path.relative_to(base_dir)}")
            cv2.imshow("Detected Person", out)
            key = cv2.waitKey(0)  # 입력 대기
            if key == 27:  # ESC
                print("강제 종료됨.")
                break
        else:
            print(f"{idx}/{len(images)}: 사람 없음 → {path.relative_to(base_dir)}")

    cv2.destroyAllWindows()
    print("모든 사진 검색이 끝났습니다.")

if __name__ == "__main__":
    # 인자 없으면 현재 폴더(.), 있으면 해당 폴더
    folder_arg = sys.argv[1] if len(sys.argv) > 1 else "."
    main(folder_arg)
