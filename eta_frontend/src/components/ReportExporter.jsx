import React, { useState } from 'react';
import { buildApiUrl } from '../api';

export function ReportExporter({ client, displayCurrency, onSuccess, onError }) {
	const today = new Date();
	const currentYear = today.getFullYear();
	const currentMonth = today.getMonth() + 1;

	const [filterType, setFilterType] = useState('monthly'); // 'monthly', 'yearly', 'custom_dates'
	const [format, setFormat] = useState('csv');
	const [year, setYear] = useState(currentYear);
	const [month, setMonth] = useState(currentMonth);
	const [startDate, setStartDate] = useState(null);
	const [endDate, setEndDate] = useState(null);
	const [startYear, setStartYear] = useState(currentYear);
	const [endYear, setEndYear] = useState(currentYear);
	const [exporting, setExporting] = useState(false);

	const months = [
		{ value: 1, label: 'January' },
		{ value: 2, label: 'February' },
		{ value: 3, label: 'March' },
		{ value: 4, label: 'April' },
		{ value: 5, label: 'May' },
		{ value: 6, label: 'June' },
		{ value: 7, label: 'July' },
		{ value: 8, label: 'August' },
		{ value: 9, label: 'September' },
		{ value: 10, label: 'October' },
		{ value: 11, label: 'November' },
		{ value: 12, label: 'December' },
	];

	// Generate years from 1900 to current year
	const years = Array.from({ length: currentYear - 1900 + 1 }, (_, i) => 1900 + i).reverse();

	const handleExport = async () => {
		setExporting(true);
		try {
			let payload = {
				target_currency: displayCurrency,
			};

			let filename = `expense_report`;

			if (filterType === 'monthly') {
				payload.period = 'monthly';
				payload.year = Number(year);
				payload.month = Number(month);
				filename = `${filename}_${year}_${String(month).padStart(2, '0')}`;
			} else if (filterType === 'yearly') {
				payload.period = 'yearly';
				payload.year = Number(year);
				filename = `${filename}_${year}`;
			} else if (filterType === 'year_range') {
				payload.period = 'year_range';
				payload.start_year = Number(startYear);
				payload.end_year = Number(endYear);
				filename = `${filename}_${startYear}_to_${endYear}`;
			} else if (filterType === 'custom_dates') {
				payload.period = 'custom_dates';
				payload.date_start = startDate;
				payload.date_end = endDate;
				filename = `${filename}_${startDate}_to_${endDate}`;
			}

			const response = await client.post(buildApiUrl(`export-report/?format=${format}`), payload, {
				responseType: 'blob',
			});

			const url = URL.createObjectURL(response.data);
			const link = document.createElement('a');
			link.href = url;
			link.download = `${filename}.${format}`;
			link.style.display = 'none';
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			setTimeout(() => URL.revokeObjectURL(url), 0);
			onSuccess(`Report exported as ${format.toUpperCase()}.`);
		} catch (error) {
			onError(error.response?.data?.detail || 'Unable to export report.');
		} finally {
			setExporting(false);
		}
	};

	return (
		<section className="card">
			<h2>Export Report</h2>

			{/* Filter Type Selection */}
			<div className="form-row">
				<label>
					Report Type
					<select className="form-control" value={filterType} onChange={(event) => setFilterType(event.target.value)}>
						<option value="monthly">Monthly</option>
						<option value="yearly">Yearly</option>
						<option value="year_range">Year Range</option>
						<option value="custom_dates">Custom Date Range</option>
					</select>
				</label>
				<label>
					Format
					<select className="form-control" value={format} onChange={(event) => setFormat(event.target.value)}>
						<option value="csv">CSV</option>
						<option value="pdf">PDF</option>
					</select>
				</label>
			</div>

			{/* Monthly Filter */}
			{filterType === 'monthly' && (
				<div className="form-row">
					<label>
						Month
						<select className="form-control" value={month} onChange={(event) => setMonth(event.target.value)}>
							{months.map((m) => (
								<option key={m.value} value={m.value}>
									{m.label}
								</option>
							))}
						</select>
					</label>
					<label>
						Year
						<select className="form-control" value={year} onChange={(event) => setYear(event.target.value)}>
							{years.map((y) => (
								<option key={y} value={y}>
									{y}
								</option>
							))}
						</select>
					</label>
				</div>
			)}

			{/* Yearly Filter */}
			{filterType === 'yearly' && (
				<div className="form-row">
					<label>
						Year
						<select className="form-control" value={year} onChange={(event) => setYear(event.target.value)}>
							{years.map((y) => (
								<option key={y} value={y}>
									{y}
								</option>
							))}
						</select>
					</label>
				</div>
			)}

			{/* Year Range Filter */}
			{filterType === 'year_range' && (
				<div className="form-row">
					<label>
						Start Year
						<select className="form-control" value={startYear} onChange={(event) => setStartYear(event.target.value)}>
							{years.map((y) => (
								<option key={y} value={y}>
									{y}
								</option>
							))}
						</select>
					</label>
					<label>
						End Year
						<select className="form-control" value={endYear} onChange={(event) => setEndYear(event.target.value)}>
							{years.map((y) => (
								<option key={y} value={y}>
									{y}
								</option>
							))}
						</select>
					</label>
				</div>
			)}

			{/* Custom Date Range Filter */}
			{filterType === 'custom_dates' && (
				<div className="form-row">
					<label>
						Start Date
						<input
							className="form-control"
							type="date"
							value={startDate}
							onChange={(event) => setStartDate(event.target.value)}
						/>
					</label>
					<label>
						End Date
						<input
							className="form-control"
							type="date"
							value={endDate}
							onChange={(event) => setEndDate(event.target.value)}
						/>
					</label>
				</div>
			)}

			<div className="report-export-actions">
				<button type="button" className="report-export-button" onClick={handleExport} disabled={exporting || (filterType === 'custom_dates' && (!startDate || !endDate))}>
					{exporting ? 'Exporting...' : 'Download Report'}
				</button>
			</div>
		</section>
	);
}
