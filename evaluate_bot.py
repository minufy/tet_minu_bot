"""현재 봇을 화면 없이 고정 시드로 반복 실행하며 성능을 기록하는 스크립트.

목적:
- 가중치·탐색 깊이 등 설정 변경 전후 성능을 수치로 비교한다.

이 스크립트로 알 수 있는 것:
- 생존성: 탑아웃까지 걸린 틱 수.
- 공격력: 게임이 집계한 총 공격량.
- 필드 상태: 최대 높이, 구멍 수, 표면 기복(change_rate).
- 내부 평가값: 현재 스코어 함수가 필드를 어떻게 점수화하는지(score_terms).
- 시드별 편차: 동일 조건에서 결과 분산/평균.

실행: python evaluate_bot.py
"""
import random
import statistics

from bot import Bot
from tet_utils.game import Game

CONTROL = {"das": 117, "arr": 0, "sdf": 0}
MAX_TICKS = 2000
THINK_TIME = 1  # ms per decision in the existing bot
SEEDS = [0, 1, 2, 3, 4]


def is_topped_out(board):
    """탑아웃 여부를 확인한다: 최상단 행에 블록이 하나라도 있으면 True."""
    top_row = board.grid[0]
    return any(cell != " " for cell in top_row)


def collect_metrics(game, bot, ticks_run):
    """에피소드 종료 시점의 간단한 지표를 수집한다."""
    heights = bot.get_heights(game.board)
    metrics = {
        "attack": getattr(game, "attack", 0),
        "ticks": ticks_run,
        "max_height": max(heights) if heights else 0,
        "holes": bot.get_holes(game.board),
        "change_rate": bot.get_change_rate(game.board),
        "score_terms": sum(bot.get_scores(game.board)),
    }
    return metrics


def run_episode(seed):
    """주어진 시드로 한 에피소드를 실행하고 지표를 반환한다."""
    random.seed(seed)
    game = Game(CONTROL)
    bot = Bot(game, THINK_TIME)

    for tick in range(1, MAX_TICKS + 1):
        for event in bot.get_events():
            type_, key = event.split(".")
            if type_ == "keydown":
                game.keydown(key)
            else:
                game.keyup(key)

        game.update(1)
        bot.update(1)

        if is_topped_out(game.board):
            return collect_metrics(game, bot, tick)

    return collect_metrics(game, bot, MAX_TICKS)


def summarize(results):
    """에피소드별 결과와 평균을 콘솔에 출력한다."""
    def mean(values):
        return round(statistics.mean(values), 3) if values else 0

    print("=== Episode Results ===")
    for i, r in enumerate(results):
        print(f"seed={SEEDS[i]} ticks={r['ticks']} attack={r['attack']} max_h={r['max_height']} holes={r['holes']} change_rate={round(r['change_rate'],3)} score_terms={round(r['score_terms'],3)}")

    print("\n=== Averages ===")
    for key in ["ticks", "attack", "max_height", "holes", "change_rate", "score_terms"]:
        print(f"{key}: {mean([r[key] for r in results])}")


def main():
    """여러 시드로 에피소드를 실행해 결과를 요약한다."""
    results = [run_episode(seed) for seed in SEEDS]
    summarize(results)


if __name__ == "__main__":
    main()
