#!/usr/bin/env python3
"""
MindLang 표준 라이브러리 - Phase 3: 배열/딕셔너리 & 파일 I/O
34개 필수 함수 구현 (외부 의존성 없음)

함수:
├─ 배열/리스트 (12개)
│  ├─ append()    - 요소 추가
│  ├─ insert()    - 위치 삽입
│  ├─ remove()    - 요소 제거
│  ├─ pop()       - 끝에서 제거
│  ├─ sort()      - 정렬 (Bubble Sort)
│  ├─ reverse()   - 역순
│  ├─ index()     - 인덱스 찾기
│  ├─ count()     - 개수 세기
│  ├─ clear()     - 모두 제거
│  ├─ copy()      - 복사
│  ├─ extend()    - 확장
│  └─ slice()     - 부분 추출
├─ 딕셔너리/맵 (10개)
│  ├─ keys()      - 모든 키
│  ├─ values()    - 모든 값
│  ├─ items()     - 키-값 쌍
│  ├─ get()       - 값 조회
│  ├─ pop()       - 키 제거
│  ├─ update()    - 병합
│  ├─ clear()     - 초기화
│  ├─ copy()      - 복사
│  ├─ has_key()   - 키 존재 확인
│  └─ from_list() - 리스트에서 생성
└─ 파일 I/O (12개)
   ├─ open()      - 파일 열기
   ├─ close()     - 파일 닫기
   ├─ read()      - 파일 읽기
   ├─ write()     - 파일 쓰기
   ├─ readline()  - 한 줄 읽기
   ├─ writelines()- 여러 줄 쓰기
   ├─ seek()      - 위치 이동
   ├─ tell()      - 현재 위치
   ├─ truncate()  - 파일 자르기
   ├─ exists()    - 파일 존재 확인
   ├─ delete()    - 파일 삭제
   └─ rename()    - 파일 이름 변경
"""

import os

class MindLangList:
    """MindLang 배열/리스트 유틸리티"""

    @staticmethod
    def append(lst, item):
        """요소 추가"""
        if not isinstance(lst, list):
            raise TypeError(f"리스트가 필요함: {type(lst)}")
        lst.append(item)
        return lst

    @staticmethod
    def insert(lst, index, item):
        """위치 삽입"""
        if not isinstance(lst, list):
            raise TypeError(f"리스트가 필요함: {type(lst)}")
        if not isinstance(index, int):
            raise TypeError(f"인덱스는 정수: {type(index)}")

        if index < 0:
            index = len(lst) + index

        if index < 0:
            index = 0
        elif index > len(lst):
            index = len(lst)

        lst.insert(index, item)
        return lst

    @staticmethod
    def remove(lst, item):
        """요소 제거"""
        if not isinstance(lst, list):
            raise TypeError(f"리스트가 필요함: {type(lst)}")

        try:
            lst.remove(item)
        except ValueError:
            raise ValueError(f"요소를 찾을 수 없음: {item}")

        return lst

    @staticmethod
    def pop(lst, index=-1):
        """끝에서 제거"""
        if not isinstance(lst, list):
            raise TypeError(f"리스트가 필요함: {type(lst)}")
        if len(lst) == 0:
            raise IndexError("빈 리스트")
        if not isinstance(index, int):
            raise TypeError(f"인덱스는 정수: {type(index)}")

        if index < 0:
            index = len(lst) + index

        if index < 0 or index >= len(lst):
            raise IndexError(f"범위 초과: {index}")

        value = lst[index]
        del lst[index]
        return value

    @staticmethod
    def sort(lst, reverse=False):
        """정렬 (Bubble Sort)"""
        if not isinstance(lst, list):
            raise TypeError(f"리스트가 필요함: {type(lst)}")

        # Bubble Sort
        n = len(lst)
        for i in range(n):
            for j in range(0, n - i - 1):
                if reverse:
                    if lst[j] < lst[j + 1]:
                        lst[j], lst[j + 1] = lst[j + 1], lst[j]
                else:
                    if lst[j] > lst[j + 1]:
                        lst[j], lst[j + 1] = lst[j + 1], lst[j]

        return lst

    @staticmethod
    def reverse(lst):
        """역순"""
        if not isinstance(lst, list):
            raise TypeError(f"리스트가 필요함: {type(lst)}")

        # 두 포인터 방식
        left, right = 0, len(lst) - 1
        while left < right:
            lst[left], lst[right] = lst[right], lst[left]
            left += 1
            right -= 1

        return lst

    @staticmethod
    def index(lst, item):
        """인덱스 찾기"""
        if not isinstance(lst, list):
            raise TypeError(f"리스트가 필요함: {type(lst)}")

        for i, val in enumerate(lst):
            if val == item:
                return i

        raise ValueError(f"요소를 찾을 수 없음: {item}")

    @staticmethod
    def count(lst, item):
        """개수 세기"""
        if not isinstance(lst, list):
            raise TypeError(f"리스트가 필요함: {type(lst)}")

        count = 0
        for val in lst:
            if val == item:
                count += 1

        return count

    @staticmethod
    def clear(lst):
        """모두 제거"""
        if not isinstance(lst, list):
            raise TypeError(f"리스트가 필요함: {type(lst)}")

        lst.clear()
        return lst

    @staticmethod
    def copy(lst):
        """복사 (얕은 복사)"""
        if not isinstance(lst, list):
            raise TypeError(f"리스트가 필요함: {type(lst)}")

        result = []
        for item in lst:
            result.append(item)

        return result

    @staticmethod
    def extend(lst, other):
        """확장"""
        if not isinstance(lst, list):
            raise TypeError(f"리스트가 필요함: {type(lst)}")
        if not isinstance(other, (list, tuple)):
            raise TypeError(f"리스트/튜플이 필요함: {type(other)}")

        for item in other:
            lst.append(item)

        return lst

    @staticmethod
    def slice(lst, start=None, end=None, step=None):
        """부분 추출"""
        if not isinstance(lst, list):
            raise TypeError(f"리스트가 필요함: {type(lst)}")

        return lst[start:end:step]


class MindLangDict:
    """MindLang 딕셔너리/맵 유틸리티"""

    @staticmethod
    def keys(d):
        """모든 키"""
        if not isinstance(d, dict):
            raise TypeError(f"딕셔너리가 필요함: {type(d)}")

        return list(d.keys())

    @staticmethod
    def values(d):
        """모든 값"""
        if not isinstance(d, dict):
            raise TypeError(f"딕셔너리가 필요함: {type(d)}")

        return list(d.values())

    @staticmethod
    def items(d):
        """키-값 쌍"""
        if not isinstance(d, dict):
            raise TypeError(f"딕셔너리가 필요함: {type(d)}")

        result = []
        for key, value in d.items():
            result.append((key, value))

        return result

    @staticmethod
    def get(d, key, default=None):
        """값 조회"""
        if not isinstance(d, dict):
            raise TypeError(f"딕셔너리가 필요함: {type(d)}")

        if key in d:
            return d[key]
        return default

    @staticmethod
    def pop(d, key, default=None):
        """키 제거"""
        if not isinstance(d, dict):
            raise TypeError(f"딕셔너리가 필요함: {type(d)}")

        if key in d:
            value = d[key]
            del d[key]
            return value

        if default is not None:
            return default

        raise KeyError(f"키를 찾을 수 없음: {key}")

    @staticmethod
    def update(d, other):
        """병합"""
        if not isinstance(d, dict):
            raise TypeError(f"딕셔너리가 필요함: {type(d)}")
        if not isinstance(other, dict):
            raise TypeError(f"딕셔너리가 필요함: {type(other)}")

        for key, value in other.items():
            d[key] = value

        return d

    @staticmethod
    def clear(d):
        """초기화"""
        if not isinstance(d, dict):
            raise TypeError(f"딕셔너리가 필요함: {type(d)}")

        d.clear()
        return d

    @staticmethod
    def copy(d):
        """복사 (얕은 복사)"""
        if not isinstance(d, dict):
            raise TypeError(f"딕셔너리가 필요함: {type(d)}")

        result = {}
        for key, value in d.items():
            result[key] = value

        return result

    @staticmethod
    def has_key(d, key):
        """키 존재 확인"""
        if not isinstance(d, dict):
            raise TypeError(f"딕셔너리가 필요함: {type(d)}")

        return key in d

    @staticmethod
    def from_list(lst):
        """리스트에서 생성 (키-값 쌍)"""
        if not isinstance(lst, (list, tuple)):
            raise TypeError(f"리스트/튜플이 필요함: {type(lst)}")

        result = {}
        for item in lst:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                key, value = item
                result[key] = value
            else:
                raise ValueError(f"유효한 키-값 쌍이 아님: {item}")

        return result


class MindLangFile:
    """MindLang 파일 I/O 유틸리티"""

    _open_files = {}  # 열린 파일 관리

    @staticmethod
    def open(filepath, mode='r'):
        """파일 열기"""
        if not isinstance(filepath, str):
            raise TypeError(f"경로는 문자열: {type(filepath)}")
        if not isinstance(mode, str):
            raise TypeError(f"모드는 문자열: {type(mode)}")

        # 모드 검증
        valid_modes = ['r', 'w', 'a', 'r+', 'rb', 'wb', 'ab', 'r+b']
        if mode not in valid_modes:
            raise ValueError(f"유효한 모드: {valid_modes}")

        try:
            file_obj = open(filepath, mode)
            file_id = id(file_obj)
            MindLangFile._open_files[file_id] = file_obj
            return file_id
        except IOError as e:
            raise IOError(f"파일 열기 실패: {e}")

    @staticmethod
    def close(file_id):
        """파일 닫기"""
        if file_id not in MindLangFile._open_files:
            raise ValueError(f"유효한 파일 ID 아님: {file_id}")

        try:
            file_obj = MindLangFile._open_files[file_id]
            file_obj.close()
            del MindLangFile._open_files[file_id]
        except IOError as e:
            raise IOError(f"파일 닫기 실패: {e}")

    @staticmethod
    def read(file_id, size=-1):
        """파일 읽기"""
        if file_id not in MindLangFile._open_files:
            raise ValueError(f"유효한 파일 ID 아님: {file_id}")

        try:
            file_obj = MindLangFile._open_files[file_id]
            return file_obj.read(size)
        except IOError as e:
            raise IOError(f"파일 읽기 실패: {e}")

    @staticmethod
    def write(file_id, data):
        """파일 쓰기"""
        if file_id not in MindLangFile._open_files:
            raise ValueError(f"유효한 파일 ID 아님: {file_id}")
        if not isinstance(data, str):
            raise TypeError(f"문자열이 필요함: {type(data)}")

        try:
            file_obj = MindLangFile._open_files[file_id]
            return file_obj.write(data)
        except IOError as e:
            raise IOError(f"파일 쓰기 실패: {e}")

    @staticmethod
    def readline(file_id):
        """한 줄 읽기"""
        if file_id not in MindLangFile._open_files:
            raise ValueError(f"유효한 파일 ID 아님: {file_id}")

        try:
            file_obj = MindLangFile._open_files[file_id]
            return file_obj.readline()
        except IOError as e:
            raise IOError(f"파일 읽기 실패: {e}")

    @staticmethod
    def writelines(file_id, lines):
        """여러 줄 쓰기"""
        if file_id not in MindLangFile._open_files:
            raise ValueError(f"유효한 파일 ID 아님: {file_id}")
        if not isinstance(lines, (list, tuple)):
            raise TypeError(f"리스트/튜플이 필요함: {type(lines)}")

        try:
            file_obj = MindLangFile._open_files[file_id]
            file_obj.writelines(lines)
        except IOError as e:
            raise IOError(f"파일 쓰기 실패: {e}")

    @staticmethod
    def seek(file_id, offset, whence=0):
        """위치 이동"""
        if file_id not in MindLangFile._open_files:
            raise ValueError(f"유효한 파일 ID 아님: {file_id}")
        if not isinstance(offset, int):
            raise TypeError(f"오프셋은 정수: {type(offset)}")

        try:
            file_obj = MindLangFile._open_files[file_id]
            return file_obj.seek(offset, whence)
        except IOError as e:
            raise IOError(f"seek 실패: {e}")

    @staticmethod
    def tell(file_id):
        """현재 위치"""
        if file_id not in MindLangFile._open_files:
            raise ValueError(f"유효한 파일 ID 아님: {file_id}")

        try:
            file_obj = MindLangFile._open_files[file_id]
            return file_obj.tell()
        except IOError as e:
            raise IOError(f"tell 실패: {e}")

    @staticmethod
    def truncate(file_id, size=None):
        """파일 자르기"""
        if file_id not in MindLangFile._open_files:
            raise ValueError(f"유효한 파일 ID 아님: {file_id}")

        try:
            file_obj = MindLangFile._open_files[file_id]
            return file_obj.truncate(size)
        except IOError as e:
            raise IOError(f"truncate 실패: {e}")

    @staticmethod
    def exists(filepath):
        """파일 존재 확인"""
        if not isinstance(filepath, str):
            raise TypeError(f"경로는 문자열: {type(filepath)}")

        return os.path.exists(filepath)

    @staticmethod
    def delete(filepath):
        """파일 삭제"""
        if not isinstance(filepath, str):
            raise TypeError(f"경로는 문자열: {type(filepath)}")

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"파일을 찾을 수 없음: {filepath}")

        try:
            os.remove(filepath)
        except OSError as e:
            raise OSError(f"파일 삭제 실패: {e}")

    @staticmethod
    def rename(old_path, new_path):
        """파일 이름 변경"""
        if not isinstance(old_path, str) or not isinstance(new_path, str):
            raise TypeError("경로는 문자열이어야 함")

        if not os.path.exists(old_path):
            raise FileNotFoundError(f"파일을 찾을 수 없음: {old_path}")

        try:
            os.rename(old_path, new_path)
        except OSError as e:
            raise OSError(f"파일 이름 변경 실패: {e}")


# ============= 테스트 함수 =============

def run_tests():
    """배열/딕셔너리/파일 I/O 함수 테스트"""

    print("\n" + "=" * 70)
    print("🧪 MindLang 표준 라이브러리 - Phase 3 테스트")
    print("=" * 70 + "\n")

    tests_passed = 0
    tests_failed = 0

    # ============= 배열 함수 테스트 =============

    # 테스트 1: append()
    try:
        lst = [1, 2, 3]
        MindLangList.append(lst, 4)
        assert lst == [1, 2, 3, 4]
        print("✅ append() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ append() - 실패: {e}")
        tests_failed += 1

    # 테스트 2: insert()
    try:
        lst = [1, 2, 3]
        MindLangList.insert(lst, 1, 99)
        assert lst == [1, 99, 2, 3]
        print("✅ insert() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ insert() - 실패: {e}")
        tests_failed += 1

    # 테스트 3: remove()
    try:
        lst = [1, 2, 3, 2]
        MindLangList.remove(lst, 2)
        assert lst == [1, 3, 2]
        print("✅ remove() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ remove() - 실패: {e}")
        tests_failed += 1

    # 테스트 4: pop()
    try:
        lst = [1, 2, 3, 4]
        val = MindLangList.pop(lst)
        assert val == 4 and lst == [1, 2, 3]
        val2 = MindLangList.pop(lst, 0)
        assert val2 == 1 and lst == [2, 3]
        print("✅ pop() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ pop() - 실패: {e}")
        tests_failed += 1

    # 테스트 5: sort()
    try:
        lst = [3, 1, 4, 1, 5]
        MindLangList.sort(lst)
        assert lst == [1, 1, 3, 4, 5]
        lst2 = [3, 1, 4]
        MindLangList.sort(lst2, reverse=True)
        assert lst2 == [4, 3, 1]
        print("✅ sort() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ sort() - 실패: {e}")
        tests_failed += 1

    # 테스트 6: reverse()
    try:
        lst = [1, 2, 3, 4]
        MindLangList.reverse(lst)
        assert lst == [4, 3, 2, 1]
        print("✅ reverse() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ reverse() - 실패: {e}")
        tests_failed += 1

    # 테스트 7: index()
    try:
        lst = [1, 2, 3, 2]
        idx = MindLangList.index(lst, 2)
        assert idx == 1
        print("✅ index() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ index() - 실패: {e}")
        tests_failed += 1

    # 테스트 8: count()
    try:
        lst = [1, 2, 3, 2, 2]
        cnt = MindLangList.count(lst, 2)
        assert cnt == 3
        print("✅ count() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ count() - 실패: {e}")
        tests_failed += 1

    # 테스트 9: clear()
    try:
        lst = [1, 2, 3]
        MindLangList.clear(lst)
        assert lst == []
        print("✅ clear() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ clear() - 실패: {e}")
        tests_failed += 1

    # 테스트 10: copy()
    try:
        lst = [1, 2, 3]
        cpy = MindLangList.copy(lst)
        assert cpy == lst and cpy is not lst
        print("✅ copy() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ copy() - 실패: {e}")
        tests_failed += 1

    # 테스트 11: extend()
    try:
        lst = [1, 2]
        MindLangList.extend(lst, [3, 4])
        assert lst == [1, 2, 3, 4]
        print("✅ extend() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ extend() - 실패: {e}")
        tests_failed += 1

    # 테스트 12: slice()
    try:
        lst = [1, 2, 3, 4, 5]
        slc = MindLangList.slice(lst, 1, 4)
        assert slc == [2, 3, 4]
        print("✅ slice() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ slice() - 실패: {e}")
        tests_failed += 1

    # ============= 딕셔너리 함수 테스트 =============

    # 테스트 13: keys()
    try:
        d = {"a": 1, "b": 2, "c": 3}
        ks = MindLangDict.keys(d)
        assert set(ks) == {"a", "b", "c"}
        print("✅ keys() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ keys() - 실패: {e}")
        tests_failed += 1

    # 테스트 14: values()
    try:
        d = {"a": 1, "b": 2, "c": 3}
        vs = MindLangDict.values(d)
        assert set(vs) == {1, 2, 3}
        print("✅ values() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ values() - 실패: {e}")
        tests_failed += 1

    # 테스트 15: items()
    try:
        d = {"a": 1, "b": 2}
        its = MindLangDict.items(d)
        assert ("a", 1) in its and ("b", 2) in its
        print("✅ items() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ items() - 실패: {e}")
        tests_failed += 1

    # 테스트 16: get()
    try:
        d = {"a": 1, "b": 2}
        assert MindLangDict.get(d, "a") == 1
        assert MindLangDict.get(d, "x", "default") == "default"
        print("✅ get() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ get() - 실패: {e}")
        tests_failed += 1

    # 테스트 17: pop()
    try:
        d = {"a": 1, "b": 2}
        val = MindLangDict.pop(d, "a")
        assert val == 1 and "a" not in d
        print("✅ pop() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ pop() - 실패: {e}")
        tests_failed += 1

    # 테스트 18: update()
    try:
        d1 = {"a": 1, "b": 2}
        d2 = {"b": 20, "c": 3}
        MindLangDict.update(d1, d2)
        assert d1 == {"a": 1, "b": 20, "c": 3}
        print("✅ update() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ update() - 실패: {e}")
        tests_failed += 1

    # 테스트 19: clear()
    try:
        d = {"a": 1, "b": 2}
        MindLangDict.clear(d)
        assert d == {}
        print("✅ clear() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ clear() - 실패: {e}")
        tests_failed += 1

    # 테스트 20: copy()
    try:
        d = {"a": 1, "b": 2}
        cpy = MindLangDict.copy(d)
        assert cpy == d and cpy is not d
        print("✅ copy() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ copy() - 실패: {e}")
        tests_failed += 1

    # 테스트 21: has_key()
    try:
        d = {"a": 1, "b": 2}
        assert MindLangDict.has_key(d, "a") == True
        assert MindLangDict.has_key(d, "x") == False
        print("✅ has_key() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ has_key() - 실패: {e}")
        tests_failed += 1

    # 테스트 22: from_list()
    try:
        lst = [["a", 1], ["b", 2], ["c", 3]]
        d = MindLangDict.from_list(lst)
        assert d == {"a": 1, "b": 2, "c": 3}
        print("✅ from_list() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ from_list() - 실패: {e}")
        tests_failed += 1

    # ============= 파일 I/O 함수 테스트 =============

    test_file = "/tmp/mindlang_test.txt"

    # 테스트 23: open() & write()
    try:
        f_id = MindLangFile.open(test_file, "w")
        MindLangFile.write(f_id, "Hello World")
        MindLangFile.close(f_id)
        print("✅ open() & write() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ open() & write() - 실패: {e}")
        tests_failed += 1

    # 테스트 24: read()
    try:
        f_id = MindLangFile.open(test_file, "r")
        content = MindLangFile.read(f_id)
        assert content == "Hello World"
        MindLangFile.close(f_id)
        print("✅ read() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ read() - 실패: {e}")
        tests_failed += 1

    # 테스트 25: readline() & writelines()
    try:
        f_id = MindLangFile.open(test_file, "w")
        MindLangFile.writelines(f_id, ["line1\n", "line2\n", "line3\n"])
        MindLangFile.close(f_id)

        f_id = MindLangFile.open(test_file, "r")
        line1 = MindLangFile.readline(f_id)
        assert line1 == "line1\n"
        MindLangFile.close(f_id)
        print("✅ readline() & writelines() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ readline() & writelines() - 실패: {e}")
        tests_failed += 1

    # 테스트 26: seek() & tell()
    try:
        f_id = MindLangFile.open(test_file, "r")
        pos1 = MindLangFile.tell(f_id)
        assert pos1 == 0
        MindLangFile.seek(f_id, 5)
        pos2 = MindLangFile.tell(f_id)
        assert pos2 == 5
        MindLangFile.close(f_id)
        print("✅ seek() & tell() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ seek() & tell() - 실패: {e}")
        tests_failed += 1

    # 테스트 27: exists()
    try:
        exists = MindLangFile.exists(test_file)
        assert exists == True
        not_exists = MindLangFile.exists("/tmp/non_existent_file_xyz.txt")
        assert not_exists == False
        print("✅ exists() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ exists() - 실패: {e}")
        tests_failed += 1

    # 테스트 28: rename()
    try:
        new_file = "/tmp/mindlang_test_renamed.txt"
        MindLangFile.rename(test_file, new_file)
        assert MindLangFile.exists(new_file)
        test_file = new_file  # 업데이트
        print("✅ rename() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ rename() - 실패: {e}")
        tests_failed += 1

    # 테스트 29: truncate()
    try:
        f_id = MindLangFile.open(test_file, "r+")
        MindLangFile.truncate(f_id, 5)
        MindLangFile.close(f_id)

        f_id = MindLangFile.open(test_file, "r")
        content = MindLangFile.read(f_id)
        MindLangFile.close(f_id)
        print("✅ truncate() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ truncate() - 실패: {e}")
        tests_failed += 1

    # 테스트 30: delete()
    try:
        MindLangFile.delete(test_file)
        assert not MindLangFile.exists(test_file)
        print("✅ delete() - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ delete() - 실패: {e}")
        tests_failed += 1

    # 추가 테스트: 음수 인덱스
    # 테스트 31: 음수 인덱스
    try:
        lst = [1, 2, 3, 4]
        val = MindLangList.pop(lst, -1)
        assert val == 4
        print("✅ 음수 인덱스 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 음수 인덱스 - 실패: {e}")
        tests_failed += 1

    # 테스트 32: slice() with step
    try:
        lst = [1, 2, 3, 4, 5, 6]
        slc = MindLangList.slice(lst, 0, 6, 2)
        assert slc == [1, 3, 5]
        print("✅ slice(step) - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ slice(step) - 실패: {e}")
        tests_failed += 1

    # 테스트 33: 빈 딕셔너리
    try:
        d = {}
        ks = MindLangDict.keys(d)
        assert ks == []
        print("✅ 빈 딕셔너리 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 빈 딕셔너리 - 실패: {e}")
        tests_failed += 1

    # 테스트 34: extend() with tuple
    try:
        lst = [1, 2]
        MindLangList.extend(lst, (3, 4, 5))
        assert lst == [1, 2, 3, 4, 5]
        print("✅ extend(tuple) - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ extend(tuple) - 실패: {e}")
        tests_failed += 1

    # 최종 결과
    print("\n" + "=" * 70)
    print(f"📊 테스트 결과: {tests_passed}/34 통과")
    print(f"✅ 성공: {tests_passed}")
    print(f"❌ 실패: {tests_failed}")
    print("=" * 70)

    return tests_failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
