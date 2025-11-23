import React from "react";

export default function Footer() {
	return (
		<footer
			role="contentinfo"
			className="relative w-full"
			style={{ background: "var(--background)" }}
		>
			<div className="max-w-6xl mx-auto py-4 px-6 text-center text-lg text-[var(--foreground)]">
				<span>
					MadHacks 2025. &nbsp;
					<span aria-hidden>©</span>
					&nbsp;Evan Cedeno, Ahmed Ismail, & Soham Mukherjee (The 3 Hacketeers)
				</span>
			</div>

			<a
				href="https://github.com/ahmedismail06/madhacks2025"
				target="_blank"
				rel="noopener noreferrer"
				aria-label="Project GitHub"
				className="absolute right-4 top-1/2 -translate-y-1/2 text-[var(--foreground)] hover:opacity-80"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="32"
					height="32"
					viewBox="0 0 24 24"
					fill="currentColor"
					aria-hidden="true"
				>
					<path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.263.82-.583 0-.287-.01-1.047-.016-2.055-3.338.726-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.757-1.333-1.757-1.09-.745.082-.73.082-.73 1.205.085 1.84 1.237 1.84 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.76-1.605-2.665-.305-5.466-1.332-5.466-5.93 0-1.31.468-2.38 1.236-3.22-.124-.303-.536-1.524.117-3.176 0 0 1.008-.322 3.3 1.23a11.52 11.52 0 013.003-.404c1.02.005 2.045.138 3.003.404 2.29-1.552 3.296-1.23 3.296-1.23.655 1.653.244 2.874.12 3.176.77.84 1.235 1.91 1.235 3.22 0 4.61-2.805 5.624-5.477 5.92.43.372.815 1.104.815 2.227 0 1.607-.015 2.903-.015 3.297 0 .322.216.701.825.582C20.565 21.796 24 17.298 24 12c0-6.63-5.37-12-12-12z" />
				</svg>
			</a>
		</footer>
	);
}
