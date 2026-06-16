import io
import base64
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') # For headless server

class CredibilityScorer:
    def __init__(self):
        # Base multiplier mappings
        self.emotion_map = {
            "confident": 0.2,
            "neutral": 0.0,
            "anxious": -0.1,
            "deceptive": -0.3,
            "angry": -0.15,
            "sad": -0.05
        }
        self.gaze_map = {
            "at_camera": 0.1,
            "away": -0.1
        }

    def compute_frame_score(self, frame: dict) -> float:
        # Base score is 50/100
        base_score = 50.0
        
        # 1. Fallacy Penalty (NLU)
        fallacy_conf = frame.get("fallacy_confidence", 0.0)
        fallacy_type = frame.get("fallacy_type", "No Fallacy")
        if fallacy_type != "No Fallacy" and fallacy_conf > 0.5:
            # e.g., 0.9 conf -> -9.0 penalty
            fallacy_penalty = -10.0 * fallacy_conf 
        else:
            fallacy_penalty = 0.0

        # 2. Fact Check Bonus/Penalty
        fc_conf = frame.get("fact_check_confidence", 0.0)
        fc_verdict = frame.get("fact_check_verdict", "unverified")
        if fc_verdict == "true":
            fc_modifier = 10.0 * fc_conf
        elif fc_verdict == "false":
            fc_modifier = -15.0 * fc_conf # Harsher penalty for false
        else:
            fc_modifier = 0.0

        # 3. Vision Modifiers (Emotion, Gaze, Gesture)
        emotion = frame.get("emotion", "neutral")
        emotion_mod = self.emotion_map.get(emotion, 0.0) * 10.0
        
        gaze = frame.get("gaze", "at_camera")
        gaze_mod = self.gaze_map.get(gaze, 0.0) * 10.0
        
        gesture = frame.get("gesture_intensity", "low")
        gesture_mod = 0.0
        if gesture == "high" and emotion == "deceptive":
            gesture_mod = -5.0 # penalty for erratic deceptive behavior

        # Sum components
        raw_score = base_score + fallacy_penalty + fc_modifier + emotion_mod + gaze_mod + gesture_mod
        
        # Bound between 0 and 100
        return max(0.0, min(100.0, raw_score))

    def analyze_timeline(self, frames: list) -> dict:
        if not frames:
            return {
                "final_score": 0,
                "trend": "neutral",
                "anomalies": [],
                "chart_base64": ""
            }

        # Compute raw scores
        raw_scores = [self.compute_frame_score(f) for f in frames]
        timestamps = [f.get("timestamp", i) for i, f in enumerate(frames)]
        
        df = pd.DataFrame({
            "timestamp": timestamps,
            "raw_score": raw_scores
        })

        # Bayesian / EMA Smoothing (alpha=0.3 for a decent smoothing factor)
        df['smoothed_score'] = df['raw_score'].ewm(alpha=0.3, adjust=False).mean()

        # Anomaly Detection (Drops > 1.5 Std Dev from mean)
        mean_score = df['smoothed_score'].mean()
        std_score = df['smoothed_score'].std()
        
        # Avoid division by zero if std is 0
        if std_score > 0:
            df['z_score'] = stats.zscore(df['smoothed_score'])
        else:
            df['z_score'] = 0.0
            
        # Anomalies are significant drops (z_score < -1.5)
        anomalies_df = df[df['z_score'] < -1.5]
        
        anomalies = []
        for _, row in anomalies_df.iterrows():
            anomalies.append({
                "timestamp": row['timestamp'],
                "score": round(row['smoothed_score'], 2)
            })

        # Calculate Trend
        if len(df) > 1:
            start_score = df['smoothed_score'].iloc[0]
            end_score = df['smoothed_score'].iloc[-1]
            diff = end_score - start_score
            if diff > 5:
                trend = "improving"
            elif diff < -5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        final_score = df['smoothed_score'].iloc[-1]

        # Generate Plot
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df['timestamp'], df['smoothed_score'], label="Credibility Score", color="#2ecc71", linewidth=2.5)
        ax.fill_between(df['timestamp'], df['smoothed_score'], 0, color="#2ecc71", alpha=0.2)
        
        # Mark anomalies
        if not anomalies_df.empty:
            ax.scatter(anomalies_df['timestamp'], anomalies_df['smoothed_score'], color="red", s=100, label="Credibility Drop", zorder=5)

        ax.set_ylim(0, 100)
        ax.set_title("Real-Time Speaker Credibility Index")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Score (0-100)")
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend()
        
        # Convert plot to Base64
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)
        chart_base64 = base64.b64encode(buf.read()).decode('utf-8')

        return {
            "final_score": round(final_score, 2),
            "trend": trend,
            "anomalies": anomalies,
            "chart_base64": chart_base64
        }
