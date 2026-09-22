import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  fetchRoadmap,
  fetchPacingEstimate,
  checkpointRetest,
} from "../api/mockapi";
import {
  fetchPathPlanningRoadmap,
  fetchResourceRecommendation,
} from "../api/realApi";

function getTier(mastery) {
  if (mastery === 0) return "locked";
  if (mastery >= 0.7) return "high";
  if (mastery >= 0.4) return "mid";
  return "low";
}

function getIcon(tier) {
  if (tier === "high") return "✓";
  if (tier === "mid") return "◐";
  if (tier === "low") return "○";
  return "🔒";
}

function Roadmap({ mastery, profile, realMastery, auth }) {
  const [topics, setTopics] = useState([]);
  const [pacing, setPacing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [animated, setAnimated] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [retestingId, setRetestingId] = useState(null);
  const [resources, setResources] = useState({});
  const navigate = useNavigate();

  const isDsa = profile?.subject === "dsa";

  useEffect(() => {
    setLoading(true);
    setAnimated(false);

    if (isDsa) {
      if (!auth?.userId) {
        setTopics([]);
        setPacing(null);
        setLoading(false);
        return;
      }
      fetchPathPlanningRoadmap(auth.userId).then((data) => {
        const mapped = [...data.roadmap]
          .sort((a, b) => a.order - b.order)
          .map((t) => ({
            id: t.topic_id,
            name: t.topic_name,
            mastery: t.mastery_score,
            isUnlocked: t.is_unlocked,
            reason: t.reason,
          }));
        setTopics(mapped);
        setPacing({
          weeklyBudget: data.weekly_budget,
          allocatedMinutes: data.allocated_minutes,
          remainingBudget: data.remaining_budget,
          totalSubtopics: data.summary.total_topics,
          completedSubtopics: data.summary.mastered_count,
          blockedCount: data.summary.blocked_count,
          remaining: data.summary.total_topics - data.summary.mastered_count,
        });
        setResources({});
        setLoading(false);
        setTimeout(() => setAnimated(true), 100);
      });
      return;
    }

    const roadmapPromise = fetchRoadmap(mastery);
    const pacingPromise = profile
      ? fetchPacingEstimate(profile.subject, mastery, profile.hours)
      : Promise.resolve(null);

    Promise.all([roadmapPromise, pacingPromise]).then(
      ([roadmapData, pacingData]) => {
        setTopics(roadmapData.topics);
        setPacing(pacingData);
        setLoading(false);
        setTimeout(() => setAnimated(true), 100);
      },
    );
  }, [mastery, profile, realMastery, isDsa, auth]);

  const toggleExpand = (id) => {
    const next = expandedId === id ? null : id;
    setExpandedId(next);
    if (next && isDsa && !resources[id]) {
      setResources((prev) => ({ ...prev, [id]: "loading" }));
      fetchResourceRecommendation(auth.userId, id)
        .then((data) => setResources((prev) => ({ ...prev, [id]: data })))
        .catch(() => setResources((prev) => ({ ...prev, [id]: "error" })));
    }
  };

  const handleRetest = async (e, topicId) => {
    e.stopPropagation();
    if (isDsa) {
      navigate("/quiz", { state: { startAt: { subject: "dsa", topicId } } });
      return;
    }
    setRetestingId(topicId);
    const checkpoint = await checkpointRetest(topicId);
    setRetestingId(null);
    if (checkpoint) {
      navigate("/quiz", { state: { startAt: checkpoint } });
    }
  };

  if (loading) {
    return (
      <div className="roadmap-container">
        <h1 className="roadmap-title">Your {isDsa ? "DSA" : ""} Roadmap</h1>
        <p className="roadmap-hint">Loading your progress...</p>
      </div>
    );
  }

  return (
    <div className="roadmap-container">
      <h1 className="roadmap-title">Your Roadmap</h1>

      {isDsa && topics.length === 0 && (
        <p className="roadmap-hint">
          Take the DSA quiz to see your progress here.
        </p>
      )}

      {pacing && !isDsa && (
        <div className="pacing-card">
          {pacing.remaining === 0 ? (
            <p>🎉 You've completed every subtopic in this subject!</p>
          ) : (
            <>
              <p className="pacing-main">
                Estimated{" "}
                <strong>
                  {pacing.estimatedDays} day
                  {pacing.estimatedDays !== 1 ? "s" : ""}
                </strong>{" "}
                to finish, at {profile.hours} hr{profile.hours > 1 ? "s" : ""}
                /day
              </p>
              <p className="pacing-sub">
                {pacing.completedSubtopics} of {pacing.totalSubtopics} subtopics
                completed · {pacing.remaining} remaining
              </p>
            </>
          )}
        </div>
      )}

      {pacing && isDsa && (
        <div className="pacing-card">
          {pacing.remaining === 0 ? (
            <p>🎉 You've mastered every DSA topic!</p>
          ) : (
            <>
              <p className="pacing-main">
                {pacing.completedSubtopics} of {pacing.totalSubtopics} topics
                mastered · {pacing.remaining} remaining
                {pacing.blockedCount > 0 &&
                  ` (${pacing.blockedCount} still locked)`}
              </p>
              <p className="pacing-sub">
                This week: {pacing.allocatedMinutes} of {pacing.weeklyBudget} min
                allocated · {pacing.remainingBudget} min left
              </p>
            </>
          )}
        </div>
      )}

      <div className="mastery-list">
        {topics.map((topic) => {
          const tier = getTier(topic.mastery);
          const isLocked = isDsa ? topic.isUnlocked === false : tier === "locked";
          const isExpanded = expandedId === topic.id;

          return (
            <div
              key={topic.id}
              className={`mastery-card ${isLocked ? "locked" : ""} ${isExpanded ? "expanded" : ""}`}
              onClick={() => !isLocked && toggleExpand(topic.id)}
            >
              <div className="mastery-row-top">
                <span className="mastery-topic">
                  <span className={`status-icon ${isLocked ? "locked" : tier}`}>
                    {isLocked ? "🔒" : getIcon(tier)}
                  </span>
                  {topic.name}
                </span>
                <span className="mastery-percent">
                  {Math.round(topic.mastery * 100)}%
                </span>
              </div>

              <div className="mastery-track">
                <div
                  className={`mastery-fill ${tier}`}
                  style={{ width: animated ? `${topic.mastery * 100}%` : "0%" }}
                />
              </div>

              {isExpanded && (
                <div className="mastery-detail">
                  {isDsa ? (
                    resources[topic.id] === "loading" || !resources[topic.id] ? (
                      <p>📚 Finding the best resource for you...</p>
                    ) : resources[topic.id] === "error" ? (
                      <p>📚 Couldn't load a resource — try again shortly.</p>
                    ) : (
                      <p>
                        📚{" "}
                        <a
                          href={resources[topic.id].resource?.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {resources[topic.id].resource?.title ??
                            "Recommended resource"}
                        </a>{" "}
                        ({resources[topic.id].selected_arm})
                      </p>
                    )
                  ) : (
                    <p>📚 {topic.resource}</p>
                  )}
                  <button
                    className="retest-btn"
                    onClick={(e) => handleRetest(e, topic.id)}
                    disabled={retestingId === topic.id}
                  >
                    {retestingId === topic.id
                      ? "Loading..."
                      : "🔁 Retest this topic"}
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <p className="roadmap-hint">
        Tap a topic to see its recommended resource
      </p>
    </div>
  );
}

export default Roadmap;
