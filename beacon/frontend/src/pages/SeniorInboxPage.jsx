import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { useAuthStore } from '../store/authStore';
import { getSeniorPendingQueries, submitSeniorAdvice, submitSeniorFAQ } from '../api/query';
import ProvisionalAnswerBox from '../components/ProvisionalAnswerBox';
import EffectsLayout from '../components/EffectsLayout';

export default function SeniorInboxPage() {
    const userId = useAuthStore((s) => s.userId);

    const [pendingQueries, setPendingQueries] = useState([]);
    const [selectedQuery, setSelectedQuery] = useState(null);
    const [loading, setLoading] = useState(true);
    const [step, setStep] = useState('advice');

    const [adviceContent, setAdviceContent] = useState('');
    const [submittingAdvice, setSubmittingAdvice] = useState(false);

    const [predictedFAQs, setPredictedFAQs] = useState([]);
    const [faqAnswers, setFaqAnswers] = useState([]);
    const [submittingFAQ, setSubmittingFAQ] = useState(false);

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
            const faqs = result.predicted_faqs || [];
            setPredictedFAQs(faqs);
            setFaqAnswers(faqs.map((q) => ({ question: q, answer: '' })));
            setStep('faq');
        } catch {
            setErrorMsg('Failed to submit advice. Please try again.');
        } finally {
            setSubmittingAdvice(false);
        }
    };

    const handleSubmitFAQ = async (e) => {
        e.preventDefault();
        setSubmittingFAQ(true);
        setErrorMsg('');
        try {
            await submitSeniorFAQ(selectedQuery.query_id, {
                senior_id: userId,
                faq_answers: faqAnswers.filter((f) => f.answer.trim()),
            });
            setPendingQueries((prev) => prev.filter((q) => q.query_id !== selectedQuery.query_id));
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
        setFaqAnswers((prev) => prev.map((item, i) => (i === index ? { ...item, answer } : item)));
    };

    return (
        <EffectsLayout
            title="Senior Inbox 📥"
            tagline="Review and respond to student queries."
        >
            {successMsg && <p className="msg-success" style={{ marginBottom: 12 }}>{successMsg}</p>}
            {errorMsg && <p className="msg-error" style={{ marginBottom: 12 }}>{errorMsg}</p>}

            <div style={{ display: 'flex', gap: 24, marginTop: 8 }}>
                {/* Left panel — query list */}
                <div style={{ flex: '0 0 320px' }}>
                    <h3 className="fx-section-title">Pending Queries ({pendingQueries.length})</h3>
                    {loading ? (
                        <p style={{ color: '#666' }}>Loading...</p>
                    ) : pendingQueries.length === 0 ? (
                        <p style={{ color: '#666' }}>No pending queries. Check back later!</p>
                    ) : (
                        pendingQueries.map((q) => (
                            <div
                                key={q.query_id}
                                onClick={() => handleSelectQuery(q)}
                                className={`list-item ${selectedQuery?.query_id === q.query_id ? 'active' : ''}`}
                                style={{ cursor: 'pointer' }}
                            >
                                <p style={{ margin: 0, fontWeight: 500, fontSize: 14, color: '#f0f0f0' }}>
                                    {(q.content || '').slice(0, 80)}{q.content?.length > 80 ? '…' : ''}
                                </p>
                                <p style={{ margin: '4px 0 0', color: '#666', fontSize: 12 }}>
                                    {q.timestamp ? new Date(q.timestamp).toLocaleDateString() : 'Recent'}
                                </p>
                            </div>
                        ))
                    )}
                </div>

                {/* Right panel */}
                <div style={{ flex: 1 }}>
                    {selectedQuery ? (
                        <>
                            {/* Step indicator */}
                            <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
                                <StepBadge num={1} label="Your Advice" active={step === 'advice'} done={step === 'faq'} />
                                <StepBadge num={2} label="Answer FAQs" active={step === 'faq'} done={false} />
                            </div>

                            {/* Question */}
                            <h3 className="fx-section-title">Student's Question</h3>
                            <div className="fx-glass" style={{ marginBottom: 16 }}>
                                <p style={{ margin: 0, lineHeight: 1.6, color: '#f0f0f0' }}>
                                    {selectedQuery.content}
                                </p>
                            </div>

                            {selectedQuery.provisional_answer && (
                                <ProvisionalAnswerBox
                                    answer={selectedQuery.provisional_answer}
                                    disclaimer="This is the AI-generated answer the student received. Please provide your expert input."
                                />
                            )}

                            {/* Step 1 */}
                            {step === 'advice' && (
                                <form onSubmit={handleSubmitAdvice} style={{ marginTop: 20 }}>
                                    <h4 style={{ color: '#f0f0f0', marginBottom: 12 }}>Write Your Expert Advice</h4>
                                    <textarea
                                        placeholder="Write your expert advice here..."
                                        value={adviceContent}
                                        onChange={(e) => setAdviceContent(e.target.value)}
                                        rows={6}
                                        className="dark-input"
                                        style={{ marginBottom: 12 }}
                                    />
                                    <button
                                        type="submit"
                                        disabled={submittingAdvice || !adviceContent.trim()}
                                        className="btn-primary"
                                    >
                                        {submittingAdvice ? 'Submitting...' : 'Submit Advice → Get FAQs'}
                                    </button>
                                </form>
                            )}

                            {/* Step 2 */}
                            {step === 'faq' && (
                                <div style={{ marginTop: 20 }}>
                                    <div className="fx-glass" style={{ borderLeft: '3px solid #22c55e', marginBottom: 16 }}>
                                        <h4 style={{ margin: '0 0 8px', color: '#22c55e', fontSize: 14 }}>
                                            ✅ Your Advice (submitted)
                                        </h4>
                                        <div style={{ color: '#f0f0f0', lineHeight: 1.6, fontSize: 14 }}>
                                            <ReactMarkdown>{adviceContent}</ReactMarkdown>
                                        </div>
                                    </div>

                                    <h4 style={{ color: '#f0f0f0', marginBottom: 8 }}>📋 Predicted Follow-up Questions</h4>
                                    <p style={{ color: '#666', fontSize: 13, marginBottom: 16 }}>
                                        Students will likely ask these follow-ups. Answer as many as you can.
                                    </p>

                                    <form onSubmit={handleSubmitFAQ}>
                                        {faqAnswers.length > 0 ? (
                                            faqAnswers.map((f, i) => (
                                                <div key={i} className="fx-glass" style={{ marginBottom: 10 }}>
                                                    <p style={{ margin: '0 0 8px', fontWeight: 600, fontSize: 14, color: '#f0f0f0' }}>
                                                        Q{i + 1}: {f.question}
                                                    </p>
                                                    <textarea
                                                        placeholder="Your answer..."
                                                        value={f.answer}
                                                        onChange={(e) => handleFaqAnswer(i, e.target.value)}
                                                        rows={3}
                                                        className="dark-input"
                                                    />
                                                </div>
                                            ))
                                        ) : (
                                            <p style={{ color: '#666' }}>
                                                No follow-up questions were generated. You can submit directly.
                                            </p>
                                        )}

                                        <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
                                            <button type="button" onClick={() => setStep('advice')} className="btn-secondary">
                                                ← Back to Edit Advice
                                            </button>
                                            <button type="submit" disabled={submittingFAQ} className="btn-success">
                                                {submittingFAQ ? 'Finalizing...' : 'Submit FAQ Answers & Resolve'}
                                            </button>
                                        </div>
                                    </form>
                                </div>
                            )}
                        </>
                    ) : (
                        <div style={{ textAlign: 'center', paddingTop: 60, color: '#666' }}>
                            <p style={{ fontSize: 18 }}>Select a query from the left panel to respond.</p>
                        </div>
                    )}
                </div>
            </div>
        </EffectsLayout>
    );
}

function StepBadge({ num, label, active, done }) {
    const bg = done ? '#22c55e' : active ? '#00b4d8' : 'rgba(255,255,255,0.06)';
    const color = done || active ? '#fff' : '#666';
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                width: 28, height: 28, borderRadius: '50%', background: bg, color,
                fontSize: 13, fontWeight: 700,
                boxShadow: active ? '0 0 10px rgba(0,180,216,0.3)' : 'none',
            }}>
                {done ? '✓' : num}
            </span>
            <span style={{
                fontWeight: active || done ? 600 : 400,
                color: active ? '#f0f0f0' : '#666', fontSize: 14
            }}>
                {label}
            </span>
        </div>
    );
}
