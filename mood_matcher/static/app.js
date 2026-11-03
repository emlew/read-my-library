// Page behavior: call the JSON API and update the DOM. No frameworks.

const form = document.querySelector("#preferences-form");
const browseButton = document.querySelector("#browse-button");
const statusEl = document.querySelector("#status");
const resultsEl = document.querySelector("#results");
const listEl = document.querySelector("#reading-list");
const listEmptyEl = document.querySelector("#list-empty");
const listCountEl = document.querySelector("#list-count");

let lastResults = []; // cards currently shown: [{ book, rationale? }], re-rendered when the list changes
let savedIds = new Set(); // ids in the reading list, used to mark "Saved" buttons

// Fetch JSON and turn non-2xx responses into thrown errors with the server's message.
async function api(url, options = {}) {
	const response = await fetch(url, options);
	if (response.status === 204) return null;
	const data = await response.json().catch(() => ({}));
	if (!response.ok) {
		throw new Error(data.error || `Request failed (${response.status})`);
	}
	return data;
}

// textContent treats book data as plain text, so it can never inject HTML.
function el(tag, className, text) {
	const node = document.createElement(tag);
	if (className) node.className = className;
	if (text !== undefined) node.textContent = text;
	return node;
}

function showStatus(message, isError = false) {
	statusEl.textContent = message;
	statusEl.classList.toggle("error", isError);
}

function resultCard({ book, rationale }) {
	const card = el("li", "card");
	card.append(
		el("h3", "card-title", book.title),
		el("p", "card-author", `by ${book.author}`),
		el("p", "card-description", book.description),
	);
	// Recommendations explain why they matched; browsed books show their tags instead.
	if (rationale) {
		card.append(el("p", "card-rationale", rationale));
	} else {
		const tags = [...book.moods, ...book.genres].join(" · ");
		card.append(el("p", "card-tags", `${tags} · ${book.reading_hours}h`));
	}

	const saved = savedIds.has(book.id);
	const button = el(
		"button",
		"save-button",
		saved ? "Saved ✓" : "Save to reading list",
	);
	button.type = "button";
	button.disabled = saved;
	button.addEventListener("click", () => saveBook(book.id, button));
	card.append(button);
	return card;
}

function renderResults() {
	resultsEl.replaceChildren(...lastResults.map(resultCard));
}

function renderReadingList(items) {
	savedIds = new Set(items.map((item) => item.book.id));
	listEmptyEl.hidden = items.length > 0;
	listCountEl.textContent = items.length ? `(${items.length})` : "";

	listEl.replaceChildren(
		...items.map(({ book }) => {
			const row = el("li", "list-item");
			const text = el("div");
			text.append(
				el("strong", "", book.title),
				el("span", "muted", ` by ${book.author}`),
			);

			const button = el("button", "remove-button", "Remove");
			button.type = "button";
			button.addEventListener("click", () => removeBook(book.id, button));
			row.append(text, button);
			return row;
		}),
	);
}

async function loadReadingList() {
	const data = await api("/api/reading-list");
	renderReadingList(data.items);
	renderResults(); // refresh Save buttons
}

async function saveBook(bookId, button) {
	button.disabled = true; // prevent double clicks while the request is in flight
	try {
		const data = await api("/api/reading-list", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ book_id: bookId }),
		});
		showStatus(`Saved ${data.book.title} to your reading list.`);
	} catch (error) {
		showStatus(error.message, true);
	}
	await loadReadingList().catch((error) => showStatus(error.message, true));
}

async function removeBook(bookId, button) {
	button.disabled = true;
	try {
		await api(`/api/reading-list/${bookId}`, { method: "DELETE" });
		showStatus("Removed book from your reading list.");
	} catch (error) {
		showStatus(error.message, true);
	}
	await loadReadingList().catch((error) => showStatus(error.message, true));
}

form.addEventListener("submit", async (event) => {
	event.preventDefault(); // stay on the page instead of a full form submission
	const params = new URLSearchParams(new FormData(form)); // mood=cozy&genre=...
	showStatus("Finding books…");

	try {
		const data = await api(`/api/recommendations?${params}`);
		lastResults = data.results;
		showStatus(
			data.count === 0
				? "No books match that combination. Try another genre or more reading time."
				: `${data.count} ${data.count === 1 ? "match" : "matches"}, best first.`,
		);
	} catch (error) {
		lastResults = [];
		showStatus(error.message, true);
	}
	renderResults();
});

browseButton.addEventListener("click", async () => {
	showStatus("Loading books…");
	try {
		const data = await api("/api/books");
		lastResults = data.books.map((book) => ({ book })); // same shape as recommendations
		showStatus(`Showing all ${data.count} books, A to Z.`);
	} catch (error) {
		lastResults = [];
		showStatus(error.message, true);
	}
	renderResults();
});

loadReadingList().catch((error) => showStatus(error.message, true));
