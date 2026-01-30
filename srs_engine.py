import math
from datetime import datetime, timedelta

class SRSEngine:
    """
    Implements the SuperMemo-2 (SM-2) Spaced Repetition Algorithm.
    Ref: https://www.supermemo.com/en/archives1990-2015/english/ol/sm2
    """

    @staticmethod
    def calculate_review(quality: int, repetition: int, efactor: float, previous_interval: int):
        """
        Calculate the next review interval and E-Factor based on user feedback.

        Args:
            quality (int): User rating (0-5).
                           5: Perfect response.
                           4: Correct response after hesitation.
                           3: Correct response recalled with serious difficulty.
                           2: Incorrect response; where the correct one seemed easy to recall.
                           1: Incorrect response; the correct one remembered.
                           0: Complete blackout.
            repetition (int): Number of successful repetitions so far.
            efactor (float): Easiness Factor (default 2.5).
            previous_interval (int): Previous interval in days.

        Returns:
            dict: {
                "interval": int (days until next review),
                "repetition": int (new repetition count),
                "efactor": float (new efactor),
                "next_review_date": datetime (timestamp provided for convenience)
            }
        """
        # 1. Update E-Factor
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_efactor = efactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        # EF cannot go below 1.3
        if new_efactor < 1.3:
            new_efactor = 1.3

        # 2. Update Repetition & Interval
        if quality >= 3:
            # Correct response
            if repetition == 0:
                interval = 1
            elif repetition == 1:
                interval = 6
            else:
                interval = math.ceil(previous_interval * new_efactor)
            
            new_repetition = repetition + 1
        else:
            # Incorrect response (reset progress)
            new_repetition = 0
            interval = 1
            # Note: In original SM-2, EF is not changed on failure, but we updated it above based on Q.
            # Some variations keep EF same on fail. We'll stick to the formula above which penalizes EF on low scores.

        next_review_date = datetime.now() + timedelta(days=interval)

        return {
            "interval": interval,
            "repetition": new_repetition,
            "efactor": round(new_efactor, 4),
            "next_review_date": next_review_date
        }

if __name__ == "__main__":
    # Simple Test
    print("Testing SM-2 Algorithm...")
    state = {"repetition": 0, "efactor": 2.5, "interval": 0}
    
    # User gets it right (Quality 4)
    res = SRSEngine.calculate_review(4, state["repetition"], state["efactor"], state["interval"])
    print(f"Review 1 (Q=4): {res}")
    
    # User gets it right again (Quality 5)
    res = SRSEngine.calculate_review(5, res["repetition"], res["efactor"], res["interval"])
    print(f"Review 2 (Q=5): {res}")
    
    # User fails (Quality 1)
    res = SRSEngine.calculate_review(1, res["repetition"], res["efactor"], res["interval"])
    print(f"Review 3 (Q=1): {res}")
