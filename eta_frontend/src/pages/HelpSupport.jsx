import { useState } from 'react';
import { SUPPORT_EMAIL } from '../config';

const FAQ_DATA = [
  {
    id: 'password-reset',
    question: 'How do I reset my password?',
    answer: "If you are logged out, click 'Forgot Password' on the login screen and enter your registered email address to receive a reset link.",
  },
  {
    id: 'social-sign-in',
    question: 'Why is Google or Apple sign-in failing?',
    answer: 'Ensure pop-ups and third-party cookies are enabled in your browser settings. Check that your browser account matches your registered email.',
  },
  {
    id: 'export-data',
    question: 'How do I export my data?',
    answer: "Navigate to the Reports page and use the export controls to download your expense report as a CSV file.",
  },
  {
    id: 'profile',
    question: 'How do I update my profile or email address?',
    answer: 'Open your account menu from the top navigation bar and select Profile to update your personal information and preferences.',
  },
];

function copyUsingFallback(value) {
  if (typeof document.execCommand !== 'function') return false;
  const input = document.createElement('textarea');
  input.value = value;
  input.setAttribute('readonly', '');
  input.style.position = 'fixed';
  input.style.opacity = '0';
  document.body.appendChild(input);
  input.select();
  const copied = document.execCommand('copy');
  input.remove();
  return copied;
}

export default function HelpSupport({ currentUser, onNavigate }) {
  const [openFaqId, setOpenFaqId] = useState(null);
  const [copyStatus, setCopyStatus] = useState('');

  const subject = encodeURIComponent('Support Request - Expense Tracker App');
  const body = encodeURIComponent(
    `Hi Support Team,\n\nI need help with:\n\n[Describe your issue here]\n\n` +
      '-----------------------------------\n' +
      `Account Email: ${currentUser?.email || 'Not logged in'}\n` +
      `User ID: ${currentUser?.id ?? 'N/A'}`,
  );
  const mailtoUrl = `mailto:${SUPPORT_EMAIL}?subject=${subject}&body=${body}`;

  async function handleCopyEmail() {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(SUPPORT_EMAIL);
      } else if (!copyUsingFallback(SUPPORT_EMAIL)) {
        throw new Error('Clipboard copy was not available.');
      }
      setCopyStatus('Email address copied.');
    } catch {
      setCopyStatus('Copy was unavailable. Select the email address below and copy it.');
    }
  }

  return (
    <main className="help-support-page">
      <div className="help-support-heading">
        {onNavigate && (
          <button type="button" className="help-support-back" onClick={() => onNavigate('dashboard')}>
            Back to app
          </button>
        )}
        <h1>Help &amp; Support</h1>
        <p>Find quick answers below or reach out directly to our team.</p>
      </div>

      <section className="help-faq-section" aria-labelledby="help-faq-heading">
        <h2 id="help-faq-heading">Frequently Asked Questions</h2>
        <div className="help-faq-list">
          {FAQ_DATA.map((faq) => {
            const isOpen = openFaqId === faq.id;
            const answerId = `faq-answer-${faq.id}`;
            return (
              <div className="help-faq-item" key={faq.id}>
                <h3>
                  <button
                    type="button"
                    className="help-faq-question"
                    aria-expanded={isOpen}
                    aria-controls={answerId}
                    onClick={() => setOpenFaqId(isOpen ? null : faq.id)}
                  >
                    <span>{faq.question}</span>
                    <span aria-hidden="true">{isOpen ? '−' : '+'}</span>
                  </button>
                </h3>
                {isOpen && <p className="help-faq-answer" id={answerId}>{faq.answer}</p>}
              </div>
            );
          })}
        </div>
      </section>

      <section className="help-contact-card" aria-labelledby="help-contact-heading">
        <h2 id="help-contact-heading">Still need help?</h2>
        <p>If your question is not answered above, send an email to our team and we will assist you.</p>
        <div className="help-contact-actions">
          <a className="help-email-link" href={mailtoUrl}>{SUPPORT_EMAIL}</a>
          <button type="button" className="help-copy-button" onClick={handleCopyEmail}>
            Copy email address
          </button>
        </div>
        <p className="help-copy-status">If the email link does not open your email app, use Copy email address.</p>
        <p className="help-copy-status" role="status" aria-live="polite">{copyStatus}</p>
      </section>
    </main>
  );
}
