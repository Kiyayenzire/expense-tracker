import React from 'react';

export function InsightsSection({ prediction = {}, insights = {}, symbol }) {
	const anomalies = insights.anomalies || [];
	const recommendations = insights.budget_recommendations || [];
	const predictionPayload = insights.predictions || prediction || {};
	const predictions = predictionPayload.predictions || predictionPayload;
	const highVolumeCategories = predictionPayload.high_volume_categories || prediction.high_volume_categories || insights.high_volume_categories || [];
	const predictedAmount = prediction.predicted_amount ?? prediction.prediction;
	const financialInsights = insights.financial_insights || [];
	const showSpendingPrediction = false;
	const showBudgetRecommendations = false;

	return (
		<section className="insights-dashboard">
			<nav className="insights-feature-nav" aria-label="Insights features">
				<a href="#natural-language-entry">Natural Language Entry</a>
				<a href="#automatic-categorization">Automatic Categorization</a>
				{showSpendingPrediction && <a href="#spending-prediction">Spending Prediction</a>}
				<a href="#anomaly-detection">Anomaly Detection</a>
				{showBudgetRecommendations && <a href="#budget-recommendations">Budget Recommendations</a>}
				<a href="#financial-insights">Financial Insights</a>
			</nav>

			<section className="card insight-feature" id="natural-language-entry">
				<h2>Natural Language Entry</h2>
				<p>Describe an expense in plain language, review the interpretation, then confirm it in the normal expense form.</p>
				<a className="insight-action" href="#/add-expense">Open Quick Expense Entry</a>
			</section>
			<section className="card insight-feature" id="automatic-categorization">
				<h2>Automatic Categorization</h2>
				<p>Quick Entry suggests a category and subcategory from the description. You can edit both before saving.</p>
			</section>
			{showSpendingPrediction && <section className="card insight-feature" id="spending-prediction">
				<h2>Spending Prediction</h2>
				{predictedAmount != null && <p>Next month forecast: {symbol}{Number(predictedAmount).toFixed(2)}</p>}
				{Object.keys(predictions).length > 0 ? <ul>{Object.entries(predictions).map(([category, amount]) => <li key={category}>{category}: {symbol}{Number(amount).toFixed(2)}</li>)}</ul> : <p>No prediction is available yet.</p>}
				{highVolumeCategories.length > 0 && <><strong>Categories With 11+ Entries</strong><ul>{highVolumeCategories.map((item) => <li key={item.category}>{item.category}: {item.entry_count} entries, forecast {symbol}{Number(item.forecast).toFixed(2)}</li>)}</ul></>}
			</section>}
			<section className="card insight-feature" id="anomaly-detection">
				<h2>Anomaly Detection</h2>
				{anomalies.length > 0 ? <ul>{anomalies.map((anomaly, index) => <li key={anomaly.id || index}>{anomaly.description || anomaly.message || String(anomaly)}</li>)}</ul> : <p>No unusual spending detected.</p>}
			</section>
			{showBudgetRecommendations && <section className="card insight-feature" id="budget-recommendations">
				<h2>Budget Recommendations</h2>
				{recommendations.length > 0 ? <ul>{recommendations.map((item) => <li key={item.category}>{item.category}: {symbol}{Number(item.recommended).toFixed(2)}</li>)}</ul> : <p>More spending history is needed for recommendations.</p>}
			</section>}
			<section className="card insight-feature" id="financial-insights">
				<h2>Financial Insights</h2>
				{financialInsights.length > 0 ? <ul>{financialInsights.map((item, index) => <li key={item.title || index}><strong>{item.title}:</strong> {item.message}</li>)}</ul> : <p>Financial insights will appear as you record expenses.</p>}
			</section>
		</section>
	);
}
