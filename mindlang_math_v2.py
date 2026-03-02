#!/usr/bin/env python3
"""
MindLang 수학 엔진 V2 - Phase 2: 선형대수 & 고급 통계
NumPy 없이 순수 Python으로 구현된 고성능 수학 라이브러리

특징:
- Vector/Matrix 클래스
- 행렬 연산 (곱셈, 전치, 역행렬, 행렬식)
- 고유값/고유벡터 계산
- 통계 분포 (정규분포, 포아송, 이항분포)
- 회귀 분석 (선형, 다항식)
- 클러스터링 (K-means, 계층적)
- 차원 축소 (PCA)
"""

import math
from typing import List, Tuple, Dict, Any


# ============= Vector 클래스 =============

class Vector:
    """벡터 클래스"""

    def __init__(self, data: List[float]):
        if not isinstance(data, list):
            raise TypeError(f"리스트가 필요함: {type(data)}")
        self.data = data
        self.size = len(data)

    def __str__(self):
        return f"Vector({self.data})"

    def __repr__(self):
        return self.__str__()

    def __add__(self, other):
        """벡터 덧셈"""
        if self.size != other.size:
            raise ValueError("벡터 크기 불일치")
        return Vector([a + b for a, b in zip(self.data, other.data)])

    def __sub__(self, other):
        """벡터 뺄셈"""
        if self.size != other.size:
            raise ValueError("벡터 크기 불일치")
        return Vector([a - b for a, b in zip(self.data, other.data)])

    def __mul__(self, scalar):
        """스칼라 곱셈"""
        if not isinstance(scalar, (int, float)):
            raise TypeError("스칼라는 숫자")
        return Vector([x * scalar for x in self.data])

    def __rmul__(self, scalar):
        """역 스칼라 곱셈"""
        return self.__mul__(scalar)

    def dot(self, other):
        """내적"""
        if self.size != other.size:
            raise ValueError("벡터 크기 불일치")
        return sum(a * b for a, b in zip(self.data, other.data))

    def cross(self, other):
        """외적 (3D 벡터만)"""
        if self.size != 3 or other.size != 3:
            raise ValueError("외적은 3D 벡터만 지원")
        return Vector([
            self.data[1] * other.data[2] - self.data[2] * other.data[1],
            self.data[2] * other.data[0] - self.data[0] * other.data[2],
            self.data[0] * other.data[1] - self.data[1] * other.data[0]
        ])

    def magnitude(self):
        """크기"""
        return math.sqrt(sum(x ** 2 for x in self.data))

    def normalize(self):
        """정규화"""
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("영벡터는 정규화 불가")
        return self * (1 / mag)

    def distance(self, other):
        """거리"""
        if self.size != other.size:
            raise ValueError("벡터 크기 불일치")
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(self.data, other.data)))


# ============= Matrix 클래스 =============

class Matrix:
    """행렬 클래스"""

    def __init__(self, data: List[List[float]]):
        if not isinstance(data, list) or not data:
            raise TypeError("행렬은 비어있지 않은 리스트")

        self.rows = len(data)
        self.cols = len(data[0])

        # 모든 행의 길이 확인
        for row in data:
            if len(row) != self.cols:
                raise ValueError("모든 행의 길이가 같아야 함")

        self.data = data

    def __str__(self):
        return f"Matrix({self.rows}x{self.cols})"

    def __repr__(self):
        return self.__str__()

    def __add__(self, other):
        """행렬 덧셈"""
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("행렬 크기 불일치")

        return Matrix([
            [self.data[i][j] + other.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ])

    def __sub__(self, other):
        """행렬 뺄셈"""
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("행렬 크기 불일치")

        return Matrix([
            [self.data[i][j] - other.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ])

    def __mul__(self, scalar):
        """스칼라 곱셈"""
        if not isinstance(scalar, (int, float)):
            raise TypeError("스칼라는 숫자")

        return Matrix([
            [x * scalar for x in row]
            for row in self.data
        ])

    def __rmul__(self, scalar):
        """역 스칼라 곱셈"""
        return self.__mul__(scalar)

    def __matmul__(self, other):
        """행렬 곱셈 (@)"""
        if self.cols != other.rows:
            raise ValueError(f"행렬 곱셈 불가능: {self.cols} != {other.rows}")

        result = []
        for i in range(self.rows):
            row = []
            for j in range(other.cols):
                val = sum(self.data[i][k] * other.data[k][j] for k in range(self.cols))
                row.append(val)
            result.append(row)

        return Matrix(result)

    def transpose(self):
        """전치"""
        return Matrix([
            [self.data[i][j] for i in range(self.rows)]
            for j in range(self.cols)
        ])

    def determinant(self):
        """행렬식"""
        if self.rows != self.cols:
            raise ValueError("행렬식은 정방행렬만 가능")

        n = self.rows

        # 1x1
        if n == 1:
            return self.data[0][0]

        # 2x2
        if n == 2:
            return self.data[0][0] * self.data[1][1] - self.data[0][1] * self.data[1][0]

        # 3x3 이상: 여인수 전개
        det = 0
        for j in range(n):
            minor = self._minor(0, j)
            cofactor = ((-1) ** j) * minor.determinant()
            det += self.data[0][j] * cofactor

        return det

    def _minor(self, row: int, col: int):
        """소행렬"""
        data = [
            [self.data[i][j] for j in range(self.cols) if j != col]
            for i in range(self.rows) if i != row
        ]
        return Matrix(data)

    def inverse(self):
        """역행렬 (2x2, 3x3)"""
        if self.rows != self.cols:
            raise ValueError("역행렬은 정방행렬만 가능")

        det = self.determinant()
        if abs(det) < 1e-10:
            raise ValueError("행렬식이 0이므로 역행렬 없음")

        n = self.rows

        if n == 2:
            # 2x2 역행렬
            return Matrix([
                [self.data[1][1] / det, -self.data[0][1] / det],
                [-self.data[1][0] / det, self.data[0][0] / det]
            ])

        if n == 3:
            # 3x3 역행렬 (수반 행렬 사용)
            adj = self._adjugate()
            return adj * (1 / det)

        raise NotImplementedError("4x4 이상은 Gaussian elimination 필요")

    def _adjugate(self):
        """수반 행렬"""
        n = self.rows
        cofactors = []

        for i in range(n):
            row = []
            for j in range(n):
                minor = self._minor(i, j)
                cofactor = ((-1) ** (i + j)) * minor.determinant()
                row.append(cofactor)
            cofactors.append(row)

        # 수반 행렬은 여인수 행렬의 전치
        adj_data = [
            [cofactors[j][i] for j in range(n)]
            for i in range(n)
        ]
        return Matrix(adj_data)

    def to_list(self):
        """리스트로 변환"""
        return self.data


# ============= 통계 분포 =============

class MindLangDistribution:
    """통계 분포"""

    @staticmethod
    def normal_pdf(x: float, mean: float = 0, std: float = 1) -> float:
        """정규분포 확률밀도함수"""
        if std <= 0:
            raise ValueError("표준편차는 양수")
        coefficient = 1 / (std * math.sqrt(2 * math.pi))
        exponent = -((x - mean) ** 2) / (2 * std ** 2)
        return coefficient * math.exp(exponent)

    @staticmethod
    def normal_cdf(x: float, mean: float = 0, std: float = 1) -> float:
        """정규분포 누적분포함수 (근사)"""
        if std <= 0:
            raise ValueError("표준편차는 양수")

        # 표준화
        z = (x - mean) / std

        # 오차함수 근사
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911

        sign = 1 if z >= 0 else -1
        z = abs(z) / math.sqrt(2)

        t = 1.0 / (1.0 + p * z)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-z * z)

        return 0.5 * (1.0 + sign * y)

    @staticmethod
    def poisson_pmf(k: int, lambda_: float) -> float:
        """포아송 분포 확률질량함수"""
        if k < 0 or lambda_ <= 0:
            raise ValueError("파라미터 범위 오류")

        # e^(-lambda) * lambda^k / k!
        numerator = math.exp(-lambda_) * (lambda_ ** k)
        denominator = math.factorial(k)
        return numerator / denominator

    @staticmethod
    def binomial_pmf(k: int, n: int, p: float) -> float:
        """이항분포 확률질량함수"""
        if not (0 <= k <= n) or not (0 <= p <= 1):
            raise ValueError("파라미터 범위 오류")

        # C(n,k) * p^k * (1-p)^(n-k)
        from math import comb
        return comb(n, k) * (p ** k) * ((1 - p) ** (n - k))

    @staticmethod
    def exponential_pdf(x: float, lambda_: float) -> float:
        """지수분포 확률밀도함수"""
        if x < 0 or lambda_ <= 0:
            raise ValueError("파라미터 범위 오류")
        return lambda_ * math.exp(-lambda_ * x)


# ============= 회귀 분석 =============

class MindLangRegression:
    """회귀 분석"""

    @staticmethod
    def linear_regression(x_values: List[float], y_values: List[float]) -> Tuple[float, float]:
        """선형 회귀 (y = mx + b)"""
        if len(x_values) != len(y_values):
            raise ValueError("x와 y의 길이 불일치")

        n = len(x_values)
        if n < 2:
            raise ValueError("최소 2개 이상의 데이터 필요")

        # 기울기와 절편 계산
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x ** 2 for x in x_values)

        m = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        b = (sum_y - m * sum_x) / n

        return m, b

    @staticmethod
    def polynomial_regression(x_values: List[float], y_values: List[float], degree: int = 2):
        """다항식 회귀"""
        if len(x_values) != len(y_values):
            raise ValueError("x와 y의 길이 불일치")

        n = len(x_values)
        if n < degree + 1:
            raise ValueError(f"최소 {degree + 1}개 이상의 데이터 필요")

        # Vandermonde 행렬 구성
        A = []
        for x in x_values:
            row = [x ** (degree - i) for i in range(degree + 1)]
            A.append(row)

        A_matrix = Matrix(A)
        y_vector = Vector(y_values)

        # 정규방정식: A^T * A * c = A^T * y
        AT = A_matrix.transpose()
        ATA = AT @ A_matrix
        ATy_data = [
            sum(A_matrix.data[i][j] * y_values[i] for i in range(n))
            for j in range(degree + 1)
        ]

        # 계수 계산 (간단한 경우만)
        if degree == 2:
            inv = ATA.inverse()
            result = inv @ Matrix([[x] for x in ATy_data])
            return [result.data[i][0] for i in range(degree + 1)]

        raise NotImplementedError("3차 이상은 고급 선형대수 필요")

    @staticmethod
    def r_squared(y_actual: List[float], y_predicted: List[float]) -> float:
        """R² (결정계수)"""
        if len(y_actual) != len(y_predicted):
            raise ValueError("y 길이 불일치")

        # 평균
        mean_y = sum(y_actual) / len(y_actual)

        # SS_tot, SS_res
        ss_tot = sum((y - mean_y) ** 2 for y in y_actual)
        ss_res = sum((y_a - y_p) ** 2 for y_a, y_p in zip(y_actual, y_predicted))

        if ss_tot == 0:
            return 0
        return 1 - (ss_res / ss_tot)


# ============= 클러스터링 =============

class MindLangClustering:
    """클러스터링"""

    @staticmethod
    def kmeans(data: List[Vector], k: int, max_iter: int = 100) -> Tuple[List[Vector], List[int]]:
        """K-means 클러스터링"""
        import random

        if len(data) < k:
            raise ValueError("데이터 수 < 클러스터 수")

        n = len(data)
        dim = data[0].size

        # 초기 중심 (무작위)
        indices = random.sample(range(n), k)
        centroids = [data[i] for i in indices]

        for iteration in range(max_iter):
            # 할당 단계
            clusters = [[] for _ in range(k)]
            assignments = []

            for i, point in enumerate(data):
                min_dist = float('inf')
                closest = 0

                for j, centroid in enumerate(centroids):
                    dist = point.distance(centroid)
                    if dist < min_dist:
                        min_dist = dist
                        closest = j

                clusters[closest].append(i)
                assignments.append(closest)

            # 업데이트 단계
            new_centroids = []
            for cluster in clusters:
                if not cluster:
                    # 빈 클러스터는 무작위로
                    new_centroids.append(data[random.randint(0, n - 1)])
                else:
                    # 평균
                    avg = Vector([0.0] * dim)
                    for idx in cluster:
                        avg = avg + data[idx]
                    avg = avg * (1 / len(cluster))
                    new_centroids.append(avg)

            # 수렴 확인
            converged = all(
                old.distance(new) < 1e-6
                for old, new in zip(centroids, new_centroids)
            )

            centroids = new_centroids

            if converged:
                break

        return centroids, assignments

    @staticmethod
    def hierarchical_clustering(data: List[Vector], method: str = "single"):
        """계층적 클러스터링"""
        n = len(data)

        # 각 포인트를 클러스터로 초기화
        clusters = [[i] for i in range(n)]
        distances = {}

        # 거리 계산
        for i in range(n):
            for j in range(i + 1, n):
                dist = data[i].distance(data[j])
                distances[(i, j)] = dist

        # 병합
        while len(clusters) > 1:
            # 가장 가까운 클러스터 찾기
            min_dist = float('inf')
            merge_i, merge_j = 0, 1

            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    # Single linkage
                    dist = min(
                        (data[a].distance(data[b]) for a in clusters[i] for b in clusters[j]),
                        default=float('inf')
                    )

                    if dist < min_dist:
                        min_dist = dist
                        merge_i, merge_j = i, j

            # 병합
            clusters[merge_i].extend(clusters[merge_j])
            clusters.pop(merge_j)

        return clusters


# ============= 차원 축소 =============

class MindLangDimensionReduction:
    """차원 축소"""

    @staticmethod
    def pca(data: List[Vector], components: int) -> Tuple[List[Vector], List[Vector]]:
        """주성분 분석 (PCA)"""
        if not data:
            raise ValueError("데이터 없음")

        n = len(data)
        dim = data[0].size

        if components > dim:
            raise ValueError(f"컴포넌트 수 > 차원 수")

        # 중심화
        mean = Vector([sum(d.data[i] for d in data) / n for i in range(dim)])
        centered = [d - mean for d in data]

        # 공분산 행렬 (간단 구현)
        cov_data = []
        for i in range(dim):
            row = []
            for j in range(dim):
                cov = sum(centered[k].data[i] * centered[k].data[j] for k in range(n)) / n
                row.append(cov)
            cov_data.append(row)

        # 주성분 추출 (Power iteration 간단 구현)
        principal_components = []
        for _ in range(components):
            import random
            v = Vector([random.random() for _ in range(dim)])
            v = v.normalize()

            # Power iteration
            for _ in range(20):
                cov_matrix = Matrix(cov_data)
                # v_new = cov @ v
                v_new_data = [
                    sum(cov_matrix.data[i][j] * v.data[j] for j in range(dim))
                    for i in range(dim)
                ]
                v_new = Vector(v_new_data)
                v = v_new.normalize()

            principal_components.append(v)

        # 데이터 변환
        transformed = []
        for d in centered:
            new_coords = [d.dot(pc) for pc in principal_components]
            transformed.append(Vector(new_coords))

        return transformed, principal_components


# ============= 테스트 =============

def run_tests():
    """테스트"""
    print("\n" + "=" * 70)
    print("🧪 MindLang 수학 엔진 V2 테스트")
    print("=" * 70 + "\n")

    tests_passed = 0
    tests_failed = 0

    # 테스트 1: Vector 연산
    try:
        v1 = Vector([1, 2, 3])
        v2 = Vector([4, 5, 6])
        v3 = v1 + v2
        assert v3.data == [5, 7, 9]
        assert v1.dot(v2) == 32
        print("✅ Vector 연산 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Vector 연산 - 실패: {e}")
        tests_failed += 1

    # 테스트 2: Matrix 연산
    try:
        m1 = Matrix([[1, 2], [3, 4]])
        m2 = Matrix([[5, 6], [7, 8]])
        m3 = m1 + m2
        assert m3.data == [[6, 8], [10, 12]]
        print("✅ Matrix 연산 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Matrix 연산 - 실패: {e}")
        tests_failed += 1

    # 테스트 3: Matrix 곱셈
    try:
        m1 = Matrix([[1, 2], [3, 4]])
        m2 = Matrix([[2, 0], [1, 2]])
        m3 = m1 @ m2
        assert m3.data == [[4, 4], [10, 8]]
        print("✅ Matrix 곱셈 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Matrix 곱셈 - 실패: {e}")
        tests_failed += 1

    # 테스트 4: 행렬식
    try:
        m = Matrix([[1, 2], [3, 4]])
        det = m.determinant()
        assert abs(det - (-2)) < 1e-10
        print("✅ 행렬식 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 행렬식 - 실패: {e}")
        tests_failed += 1

    # 테스트 5: 역행렬
    try:
        m = Matrix([[1, 2], [3, 4]])
        inv = m.inverse()
        identity = m @ inv
        for i in range(2):
            for j in range(2):
                expected = 1 if i == j else 0
                assert abs(identity.data[i][j] - expected) < 1e-10
        print("✅ 역행렬 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 역행렬 - 실패: {e}")
        tests_failed += 1

    # 테스트 6: 정규분포
    try:
        pdf = MindLangDistribution.normal_pdf(0, 0, 1)
        assert abs(pdf - 0.3989423) < 0.0001
        cdf = MindLangDistribution.normal_cdf(0, 0, 1)
        assert abs(cdf - 0.5) < 0.01
        print("✅ 정규분포 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 정규분포 - 실패: {e}")
        tests_failed += 1

    # 테스트 7: 포아송 분포
    try:
        pmf = MindLangDistribution.poisson_pmf(2, 3)
        assert pmf > 0
        print("✅ 포아송 분포 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 포아송 분포 - 실패: {e}")
        tests_failed += 1

    # 테스트 8: 선형 회귀
    try:
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        m, b = MindLangRegression.linear_regression(x, y)
        assert abs(m - 2) < 1e-10
        assert abs(b) < 1e-10
        print("✅ 선형 회귀 - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 선형 회귀 - 실패: {e}")
        tests_failed += 1

    # 테스트 9: R²
    try:
        y_actual = [2, 4, 6, 8, 10]
        y_predicted = [2, 4, 6, 8, 10]
        r2 = MindLangRegression.r_squared(y_actual, y_predicted)
        assert abs(r2 - 1.0) < 1e-10
        print("✅ R² - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ R² - 실패: {e}")
        tests_failed += 1

    # 테스트 10: K-means
    try:
        data = [Vector([0, 0]), Vector([1, 1]), Vector([10, 10]), Vector([11, 11])]
        centroids, assignments = MindLangClustering.kmeans(data, 2)
        assert len(centroids) == 2
        assert len(assignments) == 4
        print("✅ K-means - 통과")
        tests_passed += 1
    except Exception as e:
        print(f"❌ K-means - 실패: {e}")
        tests_failed += 1

    print("\n" + "=" * 70)
    print(f"📊 테스트 결과: {tests_passed}/10 통과")
    print(f"✅ 성공: {tests_passed}")
    print(f"❌ 실패: {tests_failed}")
    print("=" * 70)

    return tests_failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
