import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { fetchAdaptiveQuizBank } from "../api/mockapi";

const PASS_THRESHOLD = 0.6;

function Quiz({ mastery, setMastery, profile }) {
  const [bank, setBank] = useState([]);
  const [subjectName, setSubjectName] = useState("");
  const [loading, setLoading] = useState(true);
  const [subtopicIndex, setSubtopicIndex] = useState(0);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [phase, setPhase] = useState("testing"); // testing | fail | complete
  const navigate = useNavigate();
  const location = useLocation();

  // If we arrived here via a "Retest this topic" click on the Roadmap,
  // location.state.startAt tells us which subject/subtopic to jump straight to.
  const startAt = location.state?.startAt;
  const isRetestMode = !!startAt;

  const subject = startAt?.subject || profile?.subject || "dsa";
  const level = profile?.level || "Intermediate";

  useEffect(() => {
    setLoading(true);
    fetchAdaptiveQuizBank(subject).then((data) => {
      setBank(data.subtopics);
      setSubjectName(data.subjectName);
      setSubtopicIndex(startAt?.subtopicIndex ?? 0);
      setQuestionIndex(0);
      setAnswers({});
      setPhase("testing");
      setLoading(false);
    });
    // location.key changes on every navigation, so retesting the same topic
    // twice in a row still resets the quiz state correctly.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subject, location.key]);

  if (!profile && !isRetestMode) {
    return (
      <div className="quiz-container">
        <h1>Let's set up your profile first</h1>
        <p className="quiz-meta">
          We need a few details before starting your quiz.
        </p>
        <button
          className="quiz-next-btn enabled"
          onClick={() => navigate("/onboarding")}
        >
          Go to Onboarding
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="quiz-container">
        <p className="quiz-meta">
          Loading your {subjectName || subject} quiz...
        </p>
      </div>
    );
  }

  if (phase === "complete") {
    return (
      <div className="quiz-container">
        <h1>All Topics Complete</h1>
        <p className="quiz-meta">
          You've worked through every subtopic in {subjectName}. Check your
          Roadmap for the full picture.
        </p>
      </div>
    );
  }

  const currentSubtopic = bank[subtopicIndex];
  const questionsForLevel =
    currentSubtopic.questions[level] ||
    currentSubtopic.questions.Intermediate ||
    [];
  const currentQuestion = questionsForLevel[questionIndex];
  const isSelected = !!answers[currentQuestion?.id];
  const progressPercent =
    ((subtopicIndex + (questionIndex + 1) / questionsForLevel.length) /
      bank.length) *
    100;

  const handleSelect = (option) => {
    setAnswers({ ...answers, [currentQuestion.id]: option });
  };

  const evaluateSubtopic = () => {
    let correctCount = 0;
    questionsForLevel.forEach((q) => {
      if (answers[q.id] === q.correct) correctCount += 1;
    });
    return correctCount / questionsForLevel.length;
  };

  const advanceToNextSubtopic = (score) => {
    setMastery({
      ...mastery,
      [currentSubtopic.id]: Math.max(mastery[currentSubtopic.id] || 0, score),
    });

    // A retest is a one-off check on a single topic, not a march through the
    // rest of the subject — send the user back to the Roadmap to see the result.
    if (isRetestMode) {
      navigate("/roadmap");
      return;
    }

    if (subtopicIndex < bank.length - 1) {
      setSubtopicIndex(subtopicIndex + 1);
      setQuestionIndex(0);
      setAnswers({});
      setPhase("testing");
    } else {
      setPhase("complete");
    }
  };

  const handleNext = () => {
    if (questionIndex < questionsForLevel.length - 1) {
      setQuestionIndex(questionIndex + 1);
      return;
    }
    const score = evaluateSubtopic();
    if (score >= PASS_THRESHOLD) {
      advanceToNextSubtopic(score);
    } else {
      setMastery({
        ...mastery,
        [currentSubtopic.id]: Math.max(
          mastery[currentSubtopic.id] || 0,
          score * 0.5,
        ),
      });
      setPhase("fail");
    }
  };

  const handleRetry = () => {
    setQuestionIndex(0);
    setAnswers({});
    setPhase("testing");
  };

  if (phase === "fail") {
    return (
      <div className="quiz-container">
        <h1>Let's revisit {currentSubtopic.name}</h1>
        <p className="quiz-meta">
          You didn't quite clear this section — review the resource below, then
          retake the quiz.
        </p>
        <div className="resource-card">📚 {currentSubtopic.resource}</div>
        <button className="quiz-next-btn enabled" onClick={handleRetry}>
          I've reviewed it — Retry Quiz
        </button>
      </div>
    );
  }

  return (
    <div className="quiz-container">
      <h1>{subjectName}</h1>
      <p className="quiz-meta">
        {isRetestMode && <span className="retest-badge">🔁 Retest</span>}
        {currentSubtopic.name} · Question {questionIndex + 1} of{" "}
        {questionsForLevel.length}
        {!isRetestMode && ` · Subtopic ${subtopicIndex + 1} of ${bank.length}`}
      </p>

      <div className="quiz-progress-track">
        <div
          className="quiz-progress-fill"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <p className="quiz-question">{currentQuestion.text}</p>

      <div className="quiz-options">
        {currentQuestion.options.map((option) => (
          <button
            key={option}
            className={
              answers[currentQuestion.id] === option
                ? "quiz-option selected"
                : "quiz-option"
            }
            onClick={() => handleSelect(option)}
          >
            {option}
          </button>
        ))}
      </div>

      <button
        className={isSelected ? "quiz-next-btn enabled" : "quiz-next-btn"}
        disabled={!isSelected}
        onClick={handleNext}
      >
        {questionIndex === questionsForLevel.length - 1
          ? "Finish Subtopic"
          : "Next"}
      </button>
    </div>
  );
}

export default Quiz;
