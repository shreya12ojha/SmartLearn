import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  fetchRoadmap,
  fetchPacingEstimate,
  checkpointRetest,
} from "../api/mockapi";
import {
  fetchRoadmapReal,
  fetchNextTopicReal,
  fetchResourceRecommendation,
  getStoredAuth,
} from "../api/realApi";

const FORMAT_ICONS = {
  video: "📹",
  text: "📖",
  practice: "💻",
  interactive: "🎮",
};

function getStatusBadge(status) {
  switch (status) {
    case "MASTERED":
      return { label: "Mastered", icon: "✓", className: "badge-mastered" };
    case "SCHEDULED":
      return { label: "Scheduled", icon: "🚀", className: "badge-scheduled" };
    case "BLOCKED":
      return { label: "Blocked", icon: "🔒", className: "badge-blocked" };
    case "DEFERRED":
      return { label: "Deferred", icon: "⏳", className: "badge-deferred" };
    default:
      return { label: status, icon: "•", className: "" };
  }
}

function Roadmap({ mastery, profile, auth, realMastery }) {
  const [realRoadmapData, setRealRoadmapData] = useState(null);
  const [nextTopicRec, setNextTopicRec] = useState(null);
  const [cmabError, setCmabError] = useState("");
  const [topicResources, setTopicResources] = useState({}); // topic_id -> recommendation
  const [mockTopics, setMockTopics] = useState([]);
  const [pacing, setPacing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [animated, setAnimated] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [loadingRecId, setLoadingRecId] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const navigate = useNavigate();

  // Restore authentication from existing auth system or prop
  const currentAuth = auth || getStoredAuth();
  const effectiveUserId = currentAuth?.userId || currentAuth?.user_id || currentAuth?.user?.id;
  const effectiveToken = currentAuth?.token || currentAuth?.access_token;

  useEffect(() => {
    setLoading(true);
    setAnimated(false);
    setErrorMsg("");
    setCmabError("");

    // If an authenticated student exists, always fetch real backend roadmap
    if (effectiveUserId) {
      Promise.all([
        fetchRoadmapReal(effectiveUserId, effectiveToken),
        fetchNextTopicReal(effectiveUserId, effectiveToken).catch((err) => {
          console.warn("Could not fetch next topic separately:", err);
          return null;
        }),
      ])
        .then(async ([roadmapData, nextTopicRes]) => {
          // Use authoritative backend roadmap data
          const mergedData = { ...roadmapData };
          if (!mergedData.next_topic && nextTopicRes?.next_topic) {
            mergedData.next_topic = nextTopicRes.next_topic;
          }
          setRealRoadmapData(mergedData);

          // If there is an actual next topic, fetch its REAL CMAB recommendation
          const targetTopic = mergedData.next_topic;
          if (targetTopic && targetTopic.topic_id) {
            try {
              const rec = await fetchResourceRecommendation(
                effectiveUserId,
                targetTopic.topic_id,
                effectiveToken
              );
              setNextTopicRec(rec);
            } catch (err) {
              console.error("Could not load CMAB recommendation for next topic:", err);
              setCmabError(err.message || "Failed to load CMAB recommendation.");
              setNextTopicRec(null);
            }
          }

          setLoading(false);
          setTimeout(() => setAnimated(true), 100);
        })
        .catch((err) => {
          console.error("Path planning fetch error:", err);
          setErrorMsg(err.message || "Failed to load personalized roadmap from backend.");
          setLoading(false);
        });
      return;
    }

    // Mock branch fallback (only when genuinely unauthenticated)
    const roadmapPromise = fetchRoadmap(mastery);
    const pacingPromise = profile
      ? fetchPacingEstimate(profile.subject, mastery, profile.hours)
      : Promise.resolve(null);

    Promise.all([roadmapPromise, pacingPromise]).then(
      ([roadmapData, pacingData]) => {
        setMockTopics(roadmapData.topics);
        setPacing(pacingData);
        setLoading(false);
        setTimeout(() => setAnimated(true), 100);
      }
    );
  }, [mastery, profile, realMastery, effectiveUserId, effectiveToken]);

  const toggleExpand = async (topicId) => {
    if (expandedId === topicId) {
      setExpandedId(null);
      return;
    }

    setExpandedId(topicId);

    // If authenticated and not already fetched, load CMAB recommendation for this topic
    if (effectiveUserId && !topicResources[topicId]) {
      setLoadingRecId(topicId);
      try {
        const rec = await fetchResourceRecommendation(effectiveUserId, topicId, effectiveToken);
        setTopicResources((prev) => ({ ...prev, [topicId]: rec }));
      } catch (err) {
        console.warn(`Could not load resource for topic ${topicId}:`, err);
      } finally {
        setLoadingRecId(null);
      }
    }
  };

  const handleStartQuiz = (topicId, arm = null) => {
    // Use actual recommended arm from LinUCB/CMAB or explicit arm, without silently faking 'practice'
    const topicRec = topicResources[topicId] || (topicId === realRoadmapData?.next_topic?.topic_id ? nextTopicRec : null);
    const recommendedArm = arm || topicRec?.selected_arm || null;
    navigate("/quiz", { state: { startAt: { subject: "dsa", topicId, recommendedArm } } });
  };

  if (loading) {
    return (
      <div className="roadmap-container">
        <h1 className="roadmap-title">Your Learning Roadmap</h1>
        <p className="roadmap-hint">Planning your optimal learning path...</p>
      </div>
    );
  }

  // Render Real DSA Roadmap
  if (realRoadmapData) {
    const nextTopic = realRoadmapData.next_topic;
    const summary = realRoadmapData.summary;
    const percentAllocated = Math.min(
      100,
      Math.round((realRoadmapData.allocated_minutes / realRoadmapData.weekly_budget) * 100)
    );

    return (
      <div className="roadmap-container">
        <h1 className="roadmap-title">Personalized DSA Roadmap</h1>

        {/* 1. Next Recommended Topic Hero Section */}
        {nextTopic ? (
          <div className="next-topic-hero">
            <div className="next-topic-tag">🌟 NEXT RECOMMENDED TOPIC</div>
            <div className="next-topic-header">
              <h2>{nextTopic.topic_name}</h2>
              <span className={`difficulty-badge ${nextTopic.difficulty.toLowerCase()}`}>
                {nextTopic.difficulty}
              </span>
            </div>

            <p className="next-topic-reason">
              <strong>Why study this:</strong> {nextTopic.reason}
            </p>

            {/* CMAB Recommendation Card */}
            {nextTopicRec ? (
              <div className="cmab-recommendation-card">
                <div className="cmab-header">
                  <span className="cmab-format-pill">
                    {FORMAT_ICONS[nextTopicRec.selected_arm] || "📚"} {nextTopicRec.selected_arm.toUpperCase()} LEARNER
                  </span>
                  <span className="cmab-confidence">
                    LinUCB Score: {nextTopicRec.ucb_score.toFixed(2)}
                  </span>
                </div>

                {nextTopicRec.resource ? (
                  <div className="resource-preview">
                    <p className="resource-title">
                      <strong>Recommended Material:</strong> {nextTopicRec.resource.title}
                    </p>
                    <p className="resource-meta">
                      ⏱ Est. Time: {nextTopicRec.resource.estimated_time} mins · Difficulty: {nextTopicRec.resource.difficulty}
                    </p>
                    <div className="hero-actions">
                      <a
                        href={nextTopicRec.resource.url}
                        target="_blank"
                        rel="noreferrer"
                        className="study-btn"
                      >
                        Study {nextTopicRec.selected_arm.toUpperCase()} Now ↗
                      </a>
                      <button
                        className="quiz-action-btn"
                        onClick={() => handleStartQuiz(nextTopic.topic_id)}
                      >
                        Take Topic Quiz →
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="hero-actions">
                    <button
                      className="quiz-action-btn"
                      onClick={() => handleStartQuiz(nextTopic.topic_id)}
                    >
                      Take Topic Quiz →
                    </button>
                  </div>
                )}
              </div>
            ) : cmabError ? (
              <div className="cmab-recommendation-card">
                <p className="item-reason-text">
                  ⚠️ CMAB recommendation could not be loaded: {cmabError}
                </p>
                <div className="hero-actions">
                  <button
                    className="quiz-action-btn"
                    onClick={() => handleStartQuiz(nextTopic.topic_id)}
                  >
                    Take Topic Quiz →
                  </button>
                </div>
              </div>
            ) : (
              <div className="hero-actions">
                <button
                  className="quiz-action-btn"
                  onClick={() => handleStartQuiz(nextTopic.topic_id)}
                >
                  Take Topic Quiz →
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="all-mastered-card">
            🎉 <strong>Outstanding Achievement!</strong> You have sufficiently mastered all available topics in the curriculum!
          </div>
        )}

        {/* 2. Weekly Time Budget & Pacing Card */}
        <div className="budget-pacing-card">
          <div className="budget-header">
            <span>📅 Weekly Time Budget</span>
            <strong>
              {realRoadmapData.allocated_minutes} / {realRoadmapData.weekly_budget} mins allocated
            </strong>
          </div>
          <div className="budget-track">
            <div
              className="budget-fill"
              style={{ width: `${percentAllocated}%` }}
            />
          </div>
          <div className="pacing-metrics-grid">
            <div className="metric-pill">
              <span className="count">{summary.mastered_count}</span>
              <span className="label">Mastered</span>
            </div>
            <div className="metric-pill">
              <span className="count">{summary.scheduled_count}</span>
              <span className="label">Scheduled</span>
            </div>
            <div className="metric-pill">
              <span className="count">{summary.blocked_count}</span>
              <span className="label">Blocked</span>
            </div>
            <div className="metric-pill">
              <span className="count">{summary.deferred_count}</span>
              <span className="label">Deferred</span>
            </div>
          </div>
        </div>

        {/* 3. Ordered Roadmap Topics List */}
        <h3 className="section-subtitle">Curriculum Learning Order</h3>
        <div className="mastery-list">
          {realRoadmapData.roadmap.map((item) => {
            const badge = getStatusBadge(item.status);
            const isExpanded = expandedId === item.topic_id;
            const rec = topicResources[item.topic_id] || (item.topic_id === nextTopic?.topic_id ? nextTopicRec : null);

            return (
              <div
                key={item.topic_id}
                className={`mastery-card ${item.status.toLowerCase()} ${isExpanded ? "expanded" : ""}`}
                onClick={() => toggleExpand(item.topic_id)}
              >
                <div className="mastery-row-top">
                  <span className="mastery-topic">
                    <span className={`status-badge-inline ${badge.className}`}>
                      {badge.icon} {badge.label}
                    </span>
                    <strong>{item.order}. {item.topic_name}</strong>
                  </span>
                  <span className="mastery-percent">
                    Mastery: {Math.round(item.mastery_score * 100)}% ({item.mastery_level})
                  </span>
                </div>

                <div className="mastery-track">
                  <div
                    className={`mastery-fill ${item.status.toLowerCase()}`}
                    style={{
                      width: animated ? `${Math.max(5, item.mastery_score * 100)}%` : "0%",
                    }}
                  />
                </div>

                {/* Reason Banner */}
                <p className="item-reason-text">{item.reason}</p>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="mastery-detail">
                    {item.blocking_prerequisites?.length > 0 && (
                      <div className="blocking-box">
                        🔒 <strong>Prerequisites below 75% threshold:</strong>
                        <ul>
                          {item.blocking_prerequisites.map((p, idx) => (
                            <li key={idx}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {loadingRecId === item.topic_id ? (
                      <p className="loading-text">Loading CMAB resource recommendation...</p>
                    ) : rec?.resource ? (
                      <div className="rec-resource-box">
                        <p>
                          <strong>{FORMAT_ICONS[rec.selected_arm]} Recommended {rec.selected_arm.toUpperCase()} Resource:</strong>
                        </p>
                        <p className="res-title">{rec.resource.title}</p>
                        <p className="res-meta">
                          Est. Time: {rec.resource.estimated_time}m · {rec.resource.difficulty}
                        </p>
                        <a
                          href={rec.resource.url}
                          target="_blank"
                          rel="noreferrer"
                          className="resource-link-btn"
                          onClick={(e) => e.stopPropagation()}
                        >
                          Open Resource ↗
                        </a>
                      </div>
                    ) : (
                      <p className="loading-text">No external resource linked yet.</p>
                    )}

                    <div className="expand-action-row">
                      <button
                        className="retest-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStartQuiz(item.topic_id);
                        }}
                      >
                        {item.status === "MASTERED" ? "Retest Topic Quiz 🔁" : "Take Topic Quiz →"}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <p className="roadmap-hint">
          💡 Tap any topic card to inspect prerequisite gating, LinUCB resource suggestions, and quiz options.
        </p>
      </div>
    );
  }

  // Fallback for not logged in or mock mode
  return (
    <div className="roadmap-container">
      <h1 className="roadmap-title">Your Learning Roadmap</h1>

      {errorMsg ? (
        <div className="error-box">
          <p>{errorMsg}</p>
          <p>Please log in or ensure the backend is running at http://127.0.0.1:8000.</p>
          <button className="onboard-continue-btn" onClick={() => navigate("/")}>
            Go to Login
          </button>
        </div>
      ) : (
        <>
          <p className="roadmap-hint">
            To view your live, personalized Path Planning roadmap, please log in with your student account.
          </p>
          <button className="onboard-continue-btn" onClick={() => navigate("/")}>
            Log In to View Roadmap
          </button>
        </>
      )}
    </div>
  );
}

export default Roadmap;
