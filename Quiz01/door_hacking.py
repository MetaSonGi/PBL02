# door_hacking.py
import zipfile
import itertools
import string
import time
from datetime import datetime
import os # 파일 존재 여부 확인

def unlock_zip(zip_file_name="emergency_storage_key.zip"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_file_path = os.path.join(base_dir, zip_file_name)
    print("ZIP 파일 암호 풀기 시작!")
    print(f"목표 파일: {zip_file_path}")

    # 암호에 사용될 문자 정의 (소문자 알파벳, 숫자)
    chars = string.ascii_lowercase + string.digits
    password_length = 6

    print(f"암호는 {password_length}자리 숫자와 소문자 알파벳으로 구성됩니다.")
    total_combinations = len(chars)**password_length
    print(f"총 {total_combinations:,}가지 암호 조합을 시도합니다.")
    print("암호 해독에는 시간이 오래 걸릴 수 있습니다.")

    # ZIP 파일 존재 여부 확인
    if not os.path.exists(zip_file_path):
        print(f"오류: '{zip_file_path}' 파일이 존재하지 않습니다.")
        print("파일 경로를 확인하거나 같은 폴더에 파일을 넣어주세요.")
        return

    attempt_count = 0
    start_time = time.time()

    # 가능한 모든 암호 조합 생성 및 시도
    for attempt in itertools.product(chars, repeat=password_length):
        password = "".join(attempt) # 조합된 문자로 암호 문자열 생성
        attempt_count += 1

        # 일정 시도마다 진행 상황 출력
        if attempt_count % 100000 == 0:
            elapsed_time = time.time() - start_time
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 시도 중... {attempt_count:,}번째 | 경과 시간: {elapsed_time:.2f}초")

        try:
            # zip 파일 암호 해제 시도
            with zipfile.ZipFile(zip_file_path, 'r') as zf:
                zf.extractall(pwd=password.encode('utf-8'))
            
            # 암호 찾기 성공 시
            elapsed_time = time.time() - start_time
            print("\n암호를 찾았습니다!")
            print(f"찾아낸 암호: {password}")
            print(f"총 시도 횟수: {attempt_count:,}번")
            print(f"총 소요 시간: {elapsed_time:.2f}초")

            # 찾은 암호를 'password.txt' 파일에 저장
            with open("password.txt", "w") as f:
                f.write(password)
            print("찾은 암호가 'password.txt' 파일에 저장되었습니다.")
            return True

        except RuntimeError:
            # 암호가 틀린 경우 (에러 무시, 다음 암호 시도)
            pass
        except zipfile.BadZipFile:
            # ZIP 파일이 손상된 경우
            print(f"경고: '{zip_file_path}' 파일이 유효한 ZIP 파일이 아닙니다.")
            return False
        except Exception as e:
            # 그 외 알 수 없는 오류 발생 시
            print(f"알 수 없는 오류가 발생했어요: {e}")
            return False

    # 모든 조합을 시도했지만 암호를 찾지 못한 경우
    elapsed_time = time.time() - start_time
    print("\n모든 암호를 시도했지만 찾지 못했습니다.")
    print(f"총 시도 횟수: {attempt_count:,}번 | 총 소요 시간: {elapsed_time:.2f}초")
    return False

# 스크립트 실행 시 unlock_zip 함수 호출
if __name__ == "__main__":
    unlock_zip()
