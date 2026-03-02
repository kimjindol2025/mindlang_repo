#!/usr/bin/env python3
"""
MindLang-FreeLang 브릿지 - Phase 3: 완전 통합
FreeLang의 고성능 런타임 위에서 MindLang 실행

특징:
- FFI (Foreign Function Interface) 바인딩
- 타입 변환 시스템
- 메모리 관리 통합
- JIT 컴파일 최적화
- 성능 벤치마크
- 호환성 검증
"""

import time
import json
from typing import Any, Dict, List, Tuple, Callable
from enum import Enum


# ============= MindLang 타입 시스템 =============

class MindLangType(Enum):
    """MindLang 기본 타입"""
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOL = "bool"
    LIST = "list"
    DICT = "dict"
    VECTOR = "vector"
    MATRIX = "matrix"
    NULL = "null"


class FreeLangType(Enum):
    """FreeLang 런타임 타입"""
    I64 = "i64"          # 64-bit 정수
    F64 = "f64"          # 64-bit 부동소수점
    STR = "str"          # 문자열
    BOOL = "bool"        # 논리값
    ARRAY = "array"      # 배열
    STRUCT = "struct"    # 구조체
    PTR = "ptr"          # 포인터 (메모리 주소)


# ============= 타입 변환 시스템 =============

class TypeConverter:
    """MindLang ↔ FreeLang 타입 변환"""

    @staticmethod
    def mindlang_to_freelang(value: Any) -> Tuple[FreeLangType, Any]:
        """MindLang → FreeLang 변환"""
        if isinstance(value, bool):
            return FreeLangType.BOOL, value
        elif isinstance(value, int):
            return FreeLangType.I64, value
        elif isinstance(value, float):
            return FreeLangType.F64, value
        elif isinstance(value, str):
            return FreeLangType.STR, value
        elif isinstance(value, list):
            return FreeLangType.ARRAY, value
        elif isinstance(value, dict):
            return FreeLangType.STRUCT, value
        else:
            raise TypeError(f"변환 불가능한 타입: {type(value)}")

    @staticmethod
    def freelang_to_mindlang(freelang_type: FreeLangType, value: Any) -> Any:
        """FreeLang → MindLang 변환"""
        if freelang_type == FreeLangType.BOOL:
            return bool(value)
        elif freelang_type == FreeLangType.I64:
            return int(value)
        elif freelang_type == FreeLangType.F64:
            return float(value)
        elif freelang_type == FreeLangType.STR:
            return str(value)
        elif freelang_type == FreeLangType.ARRAY:
            return list(value)
        elif freelang_type == FreeLangType.STRUCT:
            return dict(value)
        else:
            raise TypeError(f"변환 불가능한 타입: {freelang_type}")

    @staticmethod
    def get_mindlang_type(value: Any) -> MindLangType:
        """MindLang 타입 추론"""
        if isinstance(value, bool):
            return MindLangType.BOOL
        elif isinstance(value, int):
            return MindLangType.INT
        elif isinstance(value, float):
            return MindLangType.FLOAT
        elif isinstance(value, str):
            return MindLangType.STRING
        elif isinstance(value, list):
            return MindLangType.LIST
        elif isinstance(value, dict):
            return MindLangType.DICT
        else:
            return MindLangType.NULL


# ============= 메모리 관리 =============

class MemoryManager:
    """FreeLang 호환 메모리 관리"""

    def __init__(self):
        self.allocated = {}  # {address: (size, value)}
        self.next_address = 1000000  # 시작 주소

    def allocate(self, size: int, value: Any = None) -> int:
        """메모리 할당"""
        if size <= 0:
            raise ValueError("크기는 양수여야 함")

        address = self.next_address
        self.allocated[address] = {
            'size': size,
            'value': value,
            'timestamp': time.time(),
            'accessed': 0
        }

        self.next_address += size
        return address

    def deallocate(self, address: int) -> bool:
        """메모리 해제"""
        if address not in self.allocated:
            return False

        del self.allocated[address]
        return True

    def get(self, address: int) -> Any:
        """메모리에서 읽기"""
        if address not in self.allocated:
            raise ValueError(f"할당되지 않은 주소: {address}")

        record = self.allocated[address]
        record['accessed'] += 1
        return record['value']

    def set(self, address: int, value: Any) -> None:
        """메모리에 쓰기"""
        if address not in self.allocated:
            raise ValueError(f"할당되지 않은 주소: {address}")

        self.allocated[address]['value'] = value

    def get_stats(self) -> Dict:
        """메모리 통계"""
        total_allocated = sum(r['size'] for r in self.allocated.values())
        total_accessed = sum(r['accessed'] for r in self.allocated.values())

        return {
            'blocks': len(self.allocated),
            'total_allocated': total_allocated,
            'total_accessed': total_accessed,
            'addresses': list(self.allocated.keys())
        }

    def cleanup(self, max_age: float = 3600):
        """오래된 메모리 정리"""
        current_time = time.time()
        to_delete = []

        for address, record in self.allocated.items():
            age = current_time - record['timestamp']
            if age > max_age and record['accessed'] == 0:
                to_delete.append(address)

        for address in to_delete:
            del self.allocated[address]

        return len(to_delete)


# ============= FFI 바인딩 =============

class FFIBinding:
    """FFI (Foreign Function Interface) 바인딩"""

    def __init__(self):
        self.memory = MemoryManager()
        self.functions = {}
        self.call_count = 0
        self.total_time = 0

    def register_function(self, name: str, func: Callable,
                         param_types: List[FreeLangType],
                         return_type: FreeLangType):
        """함수 등록"""
        self.functions[name] = {
            'func': func,
            'params': param_types,
            'return': return_type,
            'calls': 0,
            'total_time': 0
        }

    def call_function(self, name: str, *args) -> Any:
        """함수 호출"""
        if name not in self.functions:
            raise ValueError(f"등록되지 않은 함수: {name}")

        func_info = self.functions[name]
        func = func_info['func']

        # 타입 변환
        converted_args = []
        for i, arg in enumerate(args):
            fl_type, value = TypeConverter.mindlang_to_freelang(arg)
            converted_args.append(value)

        # 함수 실행
        start_time = time.time()
        try:
            result = func(*converted_args)
        except Exception as e:
            raise RuntimeError(f"함수 실행 오류: {e}")

        elapsed = time.time() - start_time

        # 통계 업데이트
        self.call_count += 1
        self.total_time += elapsed
        func_info['calls'] += 1
        func_info['total_time'] += elapsed

        # 결과 변환
        fl_type = func_info['return']
        return TypeConverter.freelang_to_mindlang(fl_type, result)

    def get_stats(self) -> Dict:
        """FFI 통계"""
        return {
            'total_calls': self.call_count,
            'total_time': self.total_time,
            'average_time': self.total_time / self.call_count if self.call_count > 0 else 0,
            'memory': self.memory.get_stats(),
            'functions': {
                name: {
                    'calls': info['calls'],
                    'total_time': info['total_time'],
                    'avg_time': info['total_time'] / info['calls'] if info['calls'] > 0 else 0
                }
                for name, info in self.functions.items()
            }
        }


# ============= JIT 컴파일 최적화 =============

class JITCompiler:
    """JIT 컴파일 엔진"""

    def __init__(self):
        self.cache = {}
        self.compiled = {}
        self.compilation_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def compile(self, function_name: str, code: str) -> Callable:
        """코드 컴파일"""
        # 캐시 확인
        code_hash = hash(code)
        if code_hash in self.cache:
            self.cache_hits += 1
            return self.cache[code_hash]

        self.cache_misses += 1

        # 컴파일 (간단한 exec 사용)
        try:
            namespace = {}
            exec(code, namespace)
            compiled_func = namespace.get(function_name)

            if compiled_func is None:
                raise ValueError(f"함수 '{function_name}' 컴파일 실패")

            # 캐시 저장
            self.cache[code_hash] = compiled_func
            self.compiled[function_name] = {
                'hash': code_hash,
                'time': time.time(),
                'calls': 0
            }
            self.compilation_count += 1

            return compiled_func

        except SyntaxError as e:
            raise SyntaxError(f"컴파일 오류: {e}")

    def get_stats(self) -> Dict:
        """JIT 통계"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0

        return {
            'compiled_functions': len(self.compiled),
            'cache_size': len(self.cache),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'compilation_count': self.compilation_count
        }


# ============= 완전 통합 엔진 =============

class MindLangFreeLangBridge:
    """MindLang-FreeLang 완전 통합 엔진"""

    def __init__(self):
        self.ffi = FFIBinding()
        self.jit = JITCompiler()
        self.runtime_version = "1.0.0"
        self.start_time = time.time()

    def register_stdlib_function(self, name: str, func: Callable,
                                 params: List[FreeLangType],
                                 return_type: FreeLangType):
        """표준 라이브러리 함수 등록"""
        self.ffi.register_function(name, func, params, return_type)

    def call(self, name: str, *args) -> Any:
        """함수 호출"""
        return self.ffi.call_function(name, *args)

    def compile_and_execute(self, function_name: str, code: str, *args) -> Any:
        """코드 컴파일 및 실행"""
        func = self.jit.compile(function_name, code)
        return func(*args)

    def get_performance_report(self) -> Dict:
        """성능 보고서"""
        uptime = time.time() - self.start_time

        return {
            'version': self.runtime_version,
            'uptime': f"{uptime:.2f}s",
            'ffi_stats': self.ffi.get_stats(),
            'jit_stats': self.jit.get_stats(),
            'memory': self.ffi.memory.get_stats()
        }

    def optimize_memory(self) -> int:
        """메모리 최적화"""
        return self.ffi.memory.cleanup()


# ============= 테스트 =============

def run_tests():
    """테스트"""
    print("\n" + "=" * 70)
    print("🧪 MindLang-FreeLang 브릿지 테스트")
    print("=" * 70 + "\n")

    tests_passed = 0
    tests_failed = 0

    # 테스트 1: 타입 변환
    try:
        fl_type, value = TypeConverter.mindlang_to_freelang(42)
        assert fl_type == FreeLangType.I64
        assert value == 42

        result = TypeConverter.freelang_to_mindlang(fl_type, value)
        assert result == 42

        print("✅ 타입 변환 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 타입 변환 - 실패: {e}")
        tests_failed += 1

    # 테스트 2: 메모리 할당
    try:
        mm = MemoryManager()
        addr1 = mm.allocate(100, [1, 2, 3])
        assert isinstance(addr1, int)

        value = mm.get(addr1)
        assert value == [1, 2, 3]

        mm.set(addr1, [4, 5, 6])
        value2 = mm.get(addr1)
        assert value2 == [4, 5, 6]

        mm.deallocate(addr1)
        assert addr1 not in mm.allocated

        print("✅ 메모리 할당 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 메모리 할당 - 실패: {e}")
        tests_failed += 1

    # 테스트 3: FFI 함수 등록 및 호출
    try:
        ffi = FFIBinding()

        # 함수 정의
        def add(a, b):
            return a + b

        # 등록
        ffi.register_function(
            "add",
            add,
            [FreeLangType.I64, FreeLangType.I64],
            FreeLangType.I64
        )

        # 호출
        result = ffi.call_function("add", 10, 20)
        assert result == 30

        print("✅ FFI 함수 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FFI 함수 - 실패: {e}")
        tests_failed += 1

    # 테스트 4: JIT 컴파일
    try:
        jit = JITCompiler()

        code = """
def multiply(a, b):
    return a * b
"""

        func = jit.compile("multiply", code)
        result = func(5, 6)
        assert result == 30

        # 캐시 확인
        func2 = jit.compile("multiply", code)
        assert func is func2  # 같은 객체

        print("✅ JIT 컴파일 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ JIT 컴파일 - 실패: {e}")
        tests_failed += 1

    # 테스트 5: 통합 브릿지
    try:
        bridge = MindLangFreeLangBridge()

        def square(x):
            return x * x

        bridge.register_stdlib_function(
            "square",
            square,
            [FreeLangType.F64],
            FreeLangType.F64
        )

        result = bridge.call("square", 7.0)
        assert abs(result - 49.0) < 1e-10

        report = bridge.get_performance_report()
        assert 'version' in report
        assert 'ffi_stats' in report

        print("✅ 통합 브릿지 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 통합 브릿지 - 실패: {e}")
        tests_failed += 1

    # 테스트 6: 메모리 통계
    try:
        mm = MemoryManager()
        addr1 = mm.allocate(100)
        addr2 = mm.allocate(200)

        stats = mm.get_stats()
        assert stats['blocks'] == 2
        assert stats['total_allocated'] == 300

        mm.deallocate(addr1)
        stats2 = mm.get_stats()
        assert stats2['blocks'] == 1

        print("✅ 메모리 통계 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 메모리 통계 - 실패: {e}")
        tests_failed += 1

    # 테스트 7: JIT 캐시 히트율
    try:
        jit = JITCompiler()

        code = """
def test():
    return 42
"""

        # 첫 번째 컴파일
        func1 = jit.compile("test", code)
        assert jit.cache_hits == 0
        assert jit.cache_misses == 1

        # 두 번째 컴파일 (캐시 히트)
        func2 = jit.compile("test", code)
        assert jit.cache_hits == 1
        assert jit.cache_misses == 1

        stats = jit.get_stats()
        assert "50.00%" in stats['hit_rate']

        print("✅ JIT 캐시 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ JIT 캐시 - 실패: {e}")
        tests_failed += 1

    # 테스트 8: 성능 벤치마크
    try:
        bridge = MindLangFreeLangBridge()

        def fibonacci(n):
            if n <= 1:
                return n
            a, b = 0, 1
            for _ in range(n - 1):
                a, b = b, a + b
            return b

        bridge.register_stdlib_function(
            "fib",
            fibonacci,
            [FreeLangType.I64],
            FreeLangType.I64
        )

        start = time.time()
        result = bridge.call("fib", 10)
        elapsed = time.time() - start

        assert result == 55
        assert elapsed < 1.0  # 1초 이내

        print("✅ 성능 벤치마크 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 성능 벤치마크 - 실패: {e}")
        tests_failed += 1

    print("\n" + "=" * 70)
    print(f"📊 테스트 결과: {tests_passed}/8 통과")
    print(f"✅ 성공: {tests_passed}")
    print(f"❌ 실패: {tests_failed}")
    print("=" * 70)

    return tests_failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
