import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { useAuthStore } from '../store/authStore';
import { getSeniorPendingQueries, submitSeniorAdvice, submitSeniorFAQ } from '../api/query';
import ProvisionalAnswerBox from '../components/ProvisionalAnswerBox';

/**
 * SeniorInboxPage — two-step senior response flow:
 *   Step 1: Senior writes main advice → backend returns predicted FAQs.
 *   Step 2: Senior answers FAQs → backend synthesizes final answer.
 */
export default function SeniorInboxPage() {
    const userId = useAuthStore((s) => s.userId);

    const [pendingQueries, setPendingQueries] = useState([]);
    const [selectedQuery, setSelectedQuery] = useState(null);
    const [loading, setLoading] = useState(true);

    // Step tracking: 'advice' (Step 1) or 'faq' (Step 2)
    const [step, setStep] = useState('advice');

    // Step 1 state
    const [adviceContent, setAdviceContent] = useState('');
    const [submittingAdvice, setSubmittingAdvice] = useState(false);

    // Step 2 state — FAQs returned by backend after Step 1
    const [predictedFAQs, setPredictedFAQs] = useState([]);
    const [faqAnswers, setFaqAnswers] = useState([]);
    const [submittingFAQ, setSubmittingFAQ] = useState(false);

    // Result state
    const [successMsg, setSuccessMsg] = useState('');
    const [errorMsg, setErrorMsg] = useState('');

    useEffect(() => {
        if (!userId) return;
        setLoading(true);
        getSeniorPendingQueries(userId)
            .then((data) => setPendingQueries(Array.isArray(data) ? data : []))
            .catch(() => { })
            .finally(() => setLoading(false));
    }, [userId]);

    const handleSelectQuery = (query) => {
        setSelectedQuery(query);
        setStep('advice');
        setAdviceContent('');
        setPredictedFAQs([]);
        setFaqAnswers([]);
        setSuccessMsg('');
        setErrorMsg('');
    };

    // ── Step 1: Submit main advice ──
    const handleSubmitAdvice = async (e) => {
        e.preventDefault();
        if (!selectedQuery || !adviceContent.trim()) return;

        setSubmittingAdvice(true);
        setErrorMsg('');
        try {
            const result = await submitSeniorAdvice(selectedQuery.query_id, {
                senior_id: userId,
                advice_content: adviceContent.trim(),
            });

            // Backend returns predicted FAQs
            const faqs = result.predicted_faqs || [];
            setPredictedFAQs(faqs);
            setFaqAnswers(faqs.map((q) => ({ question: q, answer: '' })));
            setStep('faq');
            setSuccessMsg('');
        } catch {
            setErrorMsg('Failed to submit advice. Please try again.');
        } finally {
            setSubmittingAdvice(false);
        }
    };

    // ── Step 2: Submit FAQ answers ──
    const handleSubmitFAQ = async (e) => {
        e.preventDefault();

        setSubmittingFAQ(true);
        setErrorMsg('');
        try {
            // Only send FAQs that have answers
            const answeredFAQs = faqAnswers.filter((f) => f.answer.trim());

            await submitSeniorFAQ(selectedQuery.query_id, {
                senior_id: userId,
                faq_answers: answeredFAQs,
            });

            // Remove from pending list, show success
            setPendingQueries((prev) =>
                prev.filter((q) => q.query_id !== selectedQuery.query_id)
            );
            setSelectedQuery(null);
            setStep('advice');
            setAdviceContent('');
            setPredictedFAQs([]);
            setFaqAnswers([]);
            setSuccessMsg('Response submitted and query resolved! ✓');
        } catch {
            setErrorMsg('Failed to submit FAQ answers. Please try again.');
        } finally {
            setSubmittingFAQ(false);
        }
    };

    const handleFaqAnswer = (index, answer) => {
        setFaqAnswers((prev) =>
            prev.map((item, i) => (i === index ? { ...item, answer } : item))
        );
    };

    return (
        <div style={{ maxWidth: 1100, margin: '2rem auto', padding: '0 16px' }}>
            <h2>Senior Inbox 📥</h2>

            {successMsg && (
                <p style={{ color: '#22c55e', fontWeight: 500, marginBottom: 12 }}>{successMsg}</p>
            )}
            {errorMsg && (
                <p style={{ color: '#ef4444', fontWeight: 500, marginBottom: 12 }}>{errorMsg}</p>
            )}

            <div style={{ display: 'flex', gap: 24, marginTop: 16 }}>
                {/* Left panel — query list */}
                <div style={{ flex: '0 0 320px' }}>
                    <h3 style={{ marginTop: 0 }}>Pending Queries ({pendingQueries.length})</h3>
                    {loading ? (
                        <p style={{ color: '#9ca3af' }}>Loading...</p>
                    ) : pendingQueries.length === 0 ? (
                        <p style={{ color: '#9ca3af' }}>No pending queries. Check back later!</p>
                    ) : (
                        pendingQueries.map((q) => (
                            <div
                                key={q.query_id}
                                onClick={() => handleSelectQuery(q)}
                                style={{
                                    border: `1px solid ${selectedQuery?.query_id === q.query_id ? '#3b82f6' : '#e5e7eb'}`,
                                    borderRadius: 10,
                                    padding: 14,
                                    marginBottom: 8,
                                    cursor: 'pointer',
                                    background: selectedQuery?.query_id === q.query_id ? '#eff6ff' : '#fff',
                                    transition: 'border-color 0.15s',
                                }}
                            >
                                <p style={{ margin: 0, fontWeight: 500, fontSize: 14 }}>
                                    {(q.content || '').slice(0, 80)}{q.content?.length > 80 ? '…' : ''}
                                </p>
                                <p style={{ margin: '4px 0 0', color: '#9ca3af', fontSize: 12 }}>
                                    {q.timestamp ? new Date(q.timestamp).toLocaleDateString() : 'Recent'}
                                </p>
                            </div>
                        ))
                    )}
                </div>

                {/* Right panel — two-step response flow */}
                <div style={{ flex: 1 }}>
                    {selectedQuery ? (
                        <>
                            {/* Step indicator */}
                            <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
                                <StepBadge
                                    num={1}
                                    label="Your Advice"
                                    active={step === 'advice'}
                                    done={step === 'faq'}
                                />
                                <StepBadge
                                    num={2}
                                    label="Answer FAQs"
                                    active={step === 'faq'}
                                    done={false}
                                />
                            </div>

                            {/* Query detail */}
                            <h3 style={{ marginTop: 0 }}>Student's Question</h3>
                            <div
                                style={{
                                    background: '#f9fafb',
                                    borderRadius: 12,
                                    padding: 16,
                                    marginBottom: 16,
                                    border: '1px solid #e5e7eb',
                                }}
                            >
                                <p style={{ margin: 0, lineHeight: 1.6 }}>{selectedQuery.content}</p>
                            </div>

                            {/* Show AI provisional answer for context */}
                            {selectedQuery.provisional_answer && (
                                <ProvisionalAnswerBox
                                    answer={selectedQuery.provisional_answer}
                                    disclaimer="This is the AI-generated answer the student received. Please provide your expert input."
                                />
                            )}

                            {/* ── STEP 1: Write advice ── */}
                            {step === 'advice' && (
                                <form onSubmit={handleSubmitAdvice} style={{ marginTop: 20 }}>
                                    <h4>Write Your Expert Advice</h4>
                                    <textarea
                                        placeholder="Write your expert advice here..."
                                        value={adviceContent}
                                        onChange={(e) => setAdviceContent(e.target.value)}
                                        rows={6}
                                        style={{
                                            width: '100%',
                                            padding: '12px',
                                            borderRadius: 10,
                                            border: '1px solid #d1d5db',
                                            fontSize: 14,
                                            resize: 'vertical',
                                            fontFamily: 'inherit',
                                            boxSizing: 'border-box',
                                        }}
                                    />
                                    <button
                                        type="submit"
                                        disabled={submittingAdvice || !adviceContent.trim()}
                                        style={{
                                            marginTop: 8,
                                            padding: '10px 24px',
                                            borderRadius: 8,
                                            border: 'none',
                                            background:
                                                submittingAdvice || !adviceContent.trim()
                                                    ? '#d1d5db'
                                                    : '#3b82f6',
                                            color: '#fff',
                                            cursor:
                                                submittingAdvice || !adviceContent.trim()
                                                    ? 'default'
                                                    : 'pointer',
                                            fontSize: 14,
                                            fontWeight: 600,
                                        }}
                                    >
                                        {submittingAdvice ? 'Submitting...' : 'Submit Advice → Get FAQs'}
                                    </button>
                                </form>
                            )}

                            {/* ── STEP 2: Answer FAQs ── */}
                            {step === 'faq' && (
                                <div style={{ marginTop: 20 }}>
                                    {/* Show submitted advice */}
                                    <div
                                        style={{
                                            background: '#f0fdf4',
                                            border: '1px solid #86efac',
                                            borderRadius: 12,
                                            padding: 16,
                                            marginBottom: 16,
                                        }}
                                    >
                                        <h4 style={{ margin: '0 0 8px', color: '#166534' }}>
                                            ✅ Your Advice (submitted)
                                        </h4>
                                        <div style={{ color: '#1f2937', lineHeight: 1.6, fontSize: 14 }}>
                                            <ReactMarkdown>{adviceContent}</ReactMarkdown>
                                        </div>
                                    </div>

                                    {/* FAQ questions from backend */}
                                    <h4>📋 Predicted Follow-up Questions</h4>
                                    <p style={{ color: '#6b7280', fontSize: 13, marginBottom: 16 }}>
                                        Students will likely ask these follow-ups. Answer as many as you can to build your knowledge base.
                                    </p>

                                    <form onSubmit={handleSubmitFAQ}>
                                        {faqAnswers.length > 0 ? (
                                            faqAnswers.map((f, i) => (
                                                <div
                                                    key={i}
                                                    style={{
                                                        border: '1px solid #e5e7eb',
                                                        borderRadius: 10,
                                                        padding: 14,
                                                        marginBottom: 10,
                                                        background: '#fff',
                                                    }}
                                                >
                                                    <p
                                                        style={{
                                                            margin: '0 0 8px',
                                                            fontWeight: 600,
                                                            fontSize: 14,
                                                            color: '#1f2937',
                                                        }}
                                                    >
                                                        Q{i + 1}: {f.question}
                                                    </p>
                                                    <textarea
                                                        placeholder="Your answer..."
                                                        value={f.answer}
                                                        onChange={(e) => handleFaqAnswer(i, e.target.value)}
                                                        rows={3}
                                                        style={{
                                                            width: '100%',
                                                            padding: '8px 12px',
                                                            borderRadius: 8,
                                                            border: '1px solid #d1d5db',
                                                            fontSize: 14,
                                                            resize: 'vertical',
                                                            fontFamily: 'inherit',
                                                            boxSizing: 'border-box',
                                                        }}
                                                    />
                                                </div>
                                            ))
                                        ) : (
                                            <p style={{ color: '#9ca3af' }}>
                                                No follow-up questions were generated. You can submit directly.
                                            </p>
                                        )}

                                        <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
                                            <button
                                                type="button"
                                                onClick={() => setStep('advice')}
                                                style={{
                                                    padding: '10px 24px',
                                                    borderRadius: 8,
                                                    border: '1px solid #d1d5db',
                                                    background: '#fff',
                                                    color: '#374151',
                                                    cursor: 'pointer',
                                                    fontSize: 14,
                                                    fontWeight: 500,
                                                }}
                                            >
                                                ← Back to Edit Advice
                                            </button>
                                            <button
                                                type="submit"
                                                disabled={submittingFAQ}
                                                style={{
                                                    padding: '10px 24px',
                                                    borderRadius: 8,
                                                    border: 'none',
                                                    background: submittingFAQ ? '#d1d5db' : '#22c55e',
                                                    color: '#fff',
                                                    cursor: submittingFAQ ? 'default' : 'pointer',
                                                    fontSize: 14,
                                                    fontWeight: 600,
                                                }}
                                            >
                                                {submittingFAQ
                                                    ? 'Finalizing...'
                                                    : 'Submit FAQ Answers & Resolve'}
                                            </button>
                                        </div>
                                    </form>
                                </div>
                            )}
                        </>
                    ) : (
                        <div style={{ textAlign: 'center', paddingTop: 60, color: '#9ca3af' }}>
                            <p style={{ fontSize: 18 }}>Select a query from the left panel to respond.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

/** Step indicator badge */
function StepBadge({ num, label, active, done }) {
    const bg = done ? '#22c55e' : active ? '#3b82f6' : '#e5e7eb';
    const color = done || active ? '#fff' : '#6b7280';
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span
                style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 28,
                    height: 28,
                    borderRadius: '50%',
                    background: bg,
                    color,
                    fontSize: 13,
                    fontWeight: 700,
                }}
            >
                {done ? '✓' : num}
            </span>
            <span style={{ fontWeight: active || done ? 600 : 400, color: active ? '#1f2937' : '#6b7280', fontSize: 14 }}>
                {label}
            </span>
        </div>
    );
}
