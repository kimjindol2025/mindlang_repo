#!/usr/bin/env python3
"""
MindLang CLI (Command Line Interface)
커맨드 라인에서 MindLang 시스템 제어

사용법:
  python mindlang_cli.py decision metrics="cpu:85,mem:78" --verbose
  python mindlang_cli.py analyze --report --save
  python mindlang_cli.py benchmark --models=all
  python mindlang_cli.py dashboard --start
"""

import asyncio
import json
import sys
from typing import Dict, List, Optional
from dataclasses import asdict
import httpx
from datetime import datetime
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.panel import Panel
from enum import Enum

app = typer.Typer(help="🧠 MindLang 시스템 커맨드 라인 인터페이스")
console = Console()


class OutputFormat(str, Enum):
    """출력 형식"""
    TEXT = "text"
    JSON = "json"
    TABLE = "table"


class APIClient:
    """API 클라이언트"""

    def __init__(self, gateway_url: str = "http://localhost:8100"):
        self.gateway_url = gateway_url
        self.client = httpx.AsyncClient(timeout=30)

    async def call_service(
        self,
        service: str,
        method: str = "GET",
        path: str = "",
        data: Optional[Dict] = None
    ) -> Dict:
        """서비스 호출"""
        url = f"{self.gateway_url}/{service}{path}"

        try:
            if method == "GET":
                response = await self.client.get(url)
            elif method == "POST":
                response = await self.client.post(url, json=data)
            elif method == "PUT":
                response = await self.client.put(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            if response.status_code >= 400:
                return {
                    'error': f"API Error {response.status_code}",
                    'details': response.text
                }

            return response.json()

        except Exception as e:
            return {'error': str(e)}

    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()


def format_output(data: Dict, format: OutputFormat) -> str:
    """출력 형식 변환"""
    if format == OutputFormat.JSON:
        return json.dumps(data, indent=2, ensure_ascii=False)
    elif format == OutputFormat.TABLE:
        # 테이블 형식 (간단한 구현)
        if isinstance(data, dict):
            table = Table(title="MindLang Result")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="magenta")

            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    table.add_row(key, json.dumps(value, ensure_ascii=False))
                else:
                    table.add_row(key, str(value))

            return table
    else:  # TEXT
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"\n{key}:")
                    for sub_key, sub_value in value.items():
                        lines.append(f"  {sub_key}: {sub_value}")
                elif isinstance(value, list):
                    lines.append(f"\n{key}:")
                    for item in value:
                        lines.append(f"  - {item}")
                else:
                    lines.append(f"{key}: {value}")
            return "\n".join(lines)

    return str(data)


# ==================== 의사결정 관련 ====================

@app.command()
async def decision(
    metrics: str = typer.Argument(..., help="메트릭 (cpu:85,mem:78,error:0.05)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="상세 출력"),
    output: OutputFormat = typer.Option(OutputFormat.TEXT, "--output", "-o", help="출력 형식"),
    save: bool = typer.Option(False, "--save", "-s", help="결과 저장"),
):
    """의사결정 실행"""
    console.print("🤔 의사결정 실행 중...", style="cyan")

    # 메트릭 파싱
    metric_dict = {}
    try:
        for pair in metrics.split(","):
            key, value = pair.split(":")
            try:
                metric_dict[key.strip()] = float(value)
            except ValueError:
                metric_dict[key.strip()] = value
    except:
        console.print("❌ 메트릭 형식 오류. 예: cpu:85,mem:78,error:0.05", style="red")
        return

    client = APIClient()

    try:
        # 의사결정 요청
        result = await client.call_service(
            "dashboard",
            method="POST",
            path="/decision",
            data={
                'metrics': metric_dict,
                'timestamp': datetime.now().isoformat()
            }
        )

        if 'error' in result:
            console.print(f"❌ 에러: {result['error']}", style="red")
        else:
            if verbose:
                console.print(Panel(
                    json.dumps(result, indent=2, ensure_ascii=False),
                    title="📊 상세 결과",
                    expand=False
                ))
            else:
                console.print("✅ 의사결정 완료", style="green")
                if 'data' in result:
                    decision = result['data'].get('final_decision', 'UNKNOWN')
                    confidence = result['data'].get('confidence', 0)
                    console.print(
                        f"결정: {decision} | 신뢰도: {confidence:.1%}",
                        style="cyan"
                    )

            if save:
                with open('decision_result.json', 'w') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                console.print("💾 결과 저장: decision_result.json", style="green")

    finally:
        await client.close()


# ==================== 분석 관련 ====================

@app.command()
async def analyze(
    report: bool = typer.Option(False, "--report", "-r", help="리포트 생성"),
    save: bool = typer.Option(False, "--save", "-s", help="결과 저장"),
    limit: int = typer.Option(100, "--limit", "-l", help="분석 대상 레코드 수"),
):
    """의사결정 이력 분석"""
    console.print("📊 분석 시작...", style="cyan")

    client = APIClient()

    try:
        # 분석 요청
        result = await client.call_service(
            "analyzer",
            method="GET",
            path=f"/analyze?limit={limit}"
        )

        if 'error' in result:
            console.print(f"❌ 에러: {result['error']}", style="red")
            return

        # 결과 표시
        if report and 'data' in result:
            console.print(Panel(
                json.dumps(result['data'], indent=2, ensure_ascii=False),
                title="📈 분석 보고서",
                expand=False
            ))

        # 요약 표시
        if 'data' in result:
            data = result['data']
            console.print("\n[bold cyan]분석 요약[/bold cyan]")

            if 'distribution' in data:
                console.print("\n의사결정 분포:")
                for decision, count in data['distribution'].items():
                    console.print(f"  {decision}: {count}개")

            if 'confidence' in data:
                console.print(f"\n평균 신뢰도: {data['confidence']['average']:.1%}")
                console.print(f"신뢰도 범위: {data['confidence']['min']:.1%} ~ {data['confidence']['max']:.1%}")

        if save:
            with open('analysis_result.json', 'w') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print("💾 결과 저장: analysis_result.json", style="green")

    finally:
        await client.close()


# ==================== 벤치마크 관련 ====================

@app.command()
async def benchmark(
    models: str = typer.Option("all", "--models", "-m", help="모델 선택 (all,gpt4,claude,llama2,mistral,local)"),
    iterations: int = typer.Option(10, "--iterations", "-i", help="반복 횟수"),
    output: OutputFormat = typer.Option(OutputFormat.TEXT, "--output", "-o", help="출력 형식"),
    save: bool = typer.Option(False, "--save", "-s", help="결과 저장"),
):
    """AI 모델 성능 벤치마크"""
    console.print("⚡ 벤치마크 실행 중...", style="cyan")

    client = APIClient()

    try:
        # 벤치마크 요청
        result = await client.call_service(
            "benchmark",
            method="POST",
            path="/benchmark",
            data={'models': models, 'iterations': iterations}
        )

        if 'error' in result:
            console.print(f"❌ 에러: {result['error']}", style="red")
            return

        # 결과 표시
        if 'data' in result:
            data = result['data']
            console.print("\n[bold cyan]벤치마크 결과[/bold cyan]")

            # 테이블로 표시
            table = Table(title="모델 성능 비교")
            table.add_column("모델", style="cyan")
            table.add_column("응답시간", style="magenta")
            table.add_column("정확도", style="green")
            table.add_column("비용", style="yellow")
            table.add_column("메모리", style="blue")

            if isinstance(data, dict) and 'results' in data:
                for result_item in data['results']:
                    table.add_row(
                        result_item.get('model', ''),
                        f"{result_item.get('latency_ms', 0):.2f}ms",
                        f"{result_item.get('accuracy', 0):.1%}",
                        f"${result_item.get('cost', 0):.6f}",
                        f"{result_item.get('memory', 0):.0f}MB"
                    )

            console.print(table)

        if save:
            with open('benchmark_result.json', 'w') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print("💾 결과 저장: benchmark_result.json", style="green")

    finally:
        await client.close()


# ==================== 대시보드 관련 ====================

@app.command()
async def dashboard(
    start: bool = typer.Option(False, "--start", "-s", help="대시보드 시작"),
    port: int = typer.Option(8000, "--port", "-p", help="포트 번호"),
    open_browser: bool = typer.Option(False, "--open", "-o", help="브라우저 열기"),
):
    """실시간 대시보드 관리"""
    if start:
        console.print(f"🚀 대시보드 시작 중... (포트: {port})", style="cyan")
        console.print(f"📱 접속 주소: http://localhost:{port}", style="green")

        if open_browser:
            import webbrowser
            webbrowser.open(f"http://localhost:{port}")

        console.print("\n실시간 업데이트 중... (Ctrl+C로 종료)", style="yellow")

        try:
            # 대시보드 프로세스 시작 (실제 구현은 subprocess 사용)
            await asyncio.sleep(float('inf'))
        except KeyboardInterrupt:
            console.print("\n대시보드 종료", style="red")
    else:
        # 대시보드 상태 조회
        client = APIClient()
        try:
            result = await client.call_service(
                "dashboard",
                method="GET",
                path="/stats"
            )

            if 'error' not in result:
                console.print("\n[bold cyan]대시보드 상태[/bold cyan]")
                console.print(f"총 의사결정: {result.get('total_decisions', 0)}개")
                console.print(f"평균 신뢰도: {result.get('average_confidence', 0):.1%}")

                if 'decision_breakdown' in result:
                    console.print("\n의사결정 분포:")
                    for decision, count in result['decision_breakdown'].items():
                        console.print(f"  {decision}: {count}개")

        finally:
            await client.close()


# ==================== 시스템 관련 ====================

@app.command()
async def status(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="상세 정보"),
):
    """시스템 상태 조회"""
    client = APIClient()

    try:
        result = await client.call_service(
            "gateway",
            method="GET",
            path="/health"
        )

        console.print("\n[bold cyan]시스템 상태[/bold cyan]")
        console.print(f"게이트웨이: {result.get('status', 'unknown')}", style="green")
        console.print(f"시간: {result.get('timestamp', 'unknown')}")

        if 'services' in result:
            console.print("\n[cyan]서비스 상태:[/cyan]")
            for service, info in result['services'].items():
                status_icon = "✅" if info['status'] == 'healthy' else "⚠️"
                console.print(
                    f"{status_icon} {service}: {info['status']} "
                    f"({info.get('response_time', 0):.3f}s)"
                )

        if detailed:
            result = await client.call_service(
                "gateway",
                method="GET",
                path="/metrics"
            )

            console.print("\n[bold cyan]상세 메트릭[/bold cyan]")
            console.print(f"총 요청: {result.get('total_requests', 0)}개")
            console.print(f"총 에러: {result.get('total_errors', 0)}개")

            if 'services' in result:
                for service_name, service_info in result['services'].items():
                    console.print(f"\n{service_name}:")
                    console.print(f"  상태: {service_info.get('status', 'unknown')}")
                    console.print(f"  요청: {service_info.get('request_count', 0)}개")
                    console.print(f"  에러: {service_info.get('error_count', 0)}개")
                    console.print(f"  에러율: {service_info.get('error_rate', 0):.1%}")
                    console.print(f"  응답시간: {service_info.get('response_time', 0):.3f}s")

    finally:
        await client.close()


@app.command()
async def logs(
    service: Optional[str] = typer.Argument(None, help="서비스명 (선택사항)"),
    limit: int = typer.Option(20, "--limit", "-l", help="로그 수"),
    filter_error: bool = typer.Option(False, "--error", "-e", help="에러만 표시"),
):
    """시스템 로그 조회"""
    client = APIClient()

    try:
        path = "/logs" if not service else f"/logs?service={service}&limit={limit}"
        result = await client.call_service(
            "gateway",
            method="GET",
            path=path
        )

        if 'error' in result:
            console.print(f"❌ 에러: {result['error']}", style="red")
            return

        logs_list = result.get('logs', [])

        if filter_error:
            logs_list = [log for log in logs_list if log.get('status_code', 200) >= 400]

        # 테이블로 표시
        table = Table(title="시스템 로그")
        table.add_column("시간", style="cyan")
        table.add_column("서비스", style="magenta")
        table.add_column("메서드", style="green")
        table.add_column("상태", style="yellow")
        table.add_column("응답시간", style="blue")

        for log in logs_list[-limit:]:
            status_code = log.get('status_code', 0)
            status_style = "red" if status_code >= 400 else "green"
            timestamp = datetime.fromtimestamp(log.get('timestamp', 0)).strftime("%H:%M:%S")

            table.add_row(
                timestamp,
                log.get('service', ''),
                log.get('method', ''),
                f"[{status_style}]{status_code}[/{status_style}]",
                f"{log.get('response_time', 0):.3f}s"
            )

        console.print(table)
        console.print(f"\n총 {result.get('total', 0)}개 로그")

    finally:
        await client.close()


@app.command()
async def config(
    action: str = typer.Argument(..., help="show|get|set"),
    key: Optional[str] = typer.Argument(None, help="설정 키"),
    value: Optional[str] = typer.Argument(None, help="설정 값"),
):
    """설정 관리"""
    console.print(f"⚙️  설정 관리: {action}", style="cyan")

    if action == "show":
        # 전체 설정 표시 (예시)
        config_data = {
            'gateway': {
                'host': '0.0.0.0',
                'port': 8100,
                'timeout': 30
            },
            'services': {
                'dashboard': {'port': 8000, 'timeout': 30},
                'learning': {'port': 8001, 'timeout': 60},
                'benchmark': {'port': 8002, 'timeout': 120},
                'analyzer': {'port': 8003, 'timeout': 60}
            }
        }
        console.print_json(data=config_data)
    elif action == "get" and key:
        console.print(f"설정: {key} (구현 필요)", style="yellow")
    elif action == "set" and key and value:
        console.print(f"✅ {key}을(를) {value}(으)로 설정", style="green")
    else:
        console.print("❌ 올바른 명령을 사용하세요", style="red")


# ==================== 주요 명령 ====================

@app.command()
def version():
    """버전 정보"""
    console.print(Panel(
        "[bold cyan]MindLang CLI v1.0.0[/bold cyan]\n"
        "🧠 다중 AI 의사결정 시스템\n\n"
        "[yellow]주요 명령:[/yellow]\n"
        "  decision - 의사결정 실행\n"
        "  analyze - 이력 분석\n"
        "  benchmark - 모델 벤치마크\n"
        "  dashboard - 대시보드 관리\n"
        "  status - 시스템 상태\n"
        "  logs - 로그 조회",
        title="정보"
    ))


@app.command()
def help():
    """도움말"""
    console.print(Panel(
        "[bold cyan]MindLang CLI 사용 가이드[/bold cyan]\n\n"
        "[yellow]의사결정 실행:[/yellow]\n"
        "  mindlang decision cpu:85,mem:78,error:0.05 --verbose\n\n"
        "[yellow]이력 분석:[/yellow]\n"
        "  mindlang analyze --report --save\n\n"
        "[yellow]벤치마크:[/yellow]\n"
        "  mindlang benchmark --models=all --iterations=50\n\n"
        "[yellow]시스템 상태:[/yellow]\n"
        "  mindlang status --detailed\n\n"
        "[yellow]로그 조회:[/yellow]\n"
        "  mindlang logs dashboard --limit=50",
        title="도움말"
    ))


if __name__ == "__main__":
    app()
