const state = { game: null, keeps: new Set(), busy: false };

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

async function request(path, body = null) {
  const options = body === null ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

function categoryRow(category) {
  const score = category.used ? category.score : category.preview;
  const qualifies = category.section === "Accolades" && !category.used && (category.preview ?? 0) > 0;
  const elite = !category.used && category.glow_threshold && (category.preview ?? 0) >= category.glow_threshold;
  const scoredHighlight = category.used && (
    (category.section === "Accolades" && category.score > 0) ||
    (category.glow_threshold && category.score >= category.glow_threshold)
  );
  const detail = category.used && category.selection
    ? `${category.selection.player} · ${category.selection.season} ${category.selection.team}`
    : category.preview !== null ? "Score this player" : "Spin to preview";
  const valueLabel = category.formula || (category.fixed_value ? `${category.fixed_value} pts` : "");
  const icon = category.icon ? `<i class="category-icon" aria-hidden="true">${category.icon}</i>` : "";
  const classes = [category.used && "used", qualifies && "qualified", elite && "elite", scoredHighlight && "scored-highlight"].filter(Boolean).join(" ");
  return `<button class="category ${classes}" data-category="${category.id}" ${category.used || category.preview === null ? "disabled" : ""}>
    ${icon}<span class="category-copy"><strong>${category.label} <em>${valueLabel}</em></strong><small>${detail}</small></span>
    <b>${score ?? "—"}</b>
  </button>`;
}

function render(game) {
  state.game = game;
  $("#turn-label").textContent = game.complete ? "Game complete" : `Turn ${game.turn} / ${game.turns_total}`;
  $("#spin-label").textContent = game.spins_used
    ? `Spin ${game.spins_used} / ${game.spins_total} · ${game.rerolls_left} rerolls left`
    : "Ready to spin";
  $("#total-score").textContent = game.total_score;
  $("#upper-score").textContent = game.upper_total;
  $("#bonus-score").textContent = game.bonus ? `+${game.bonus}` : "0";

  const player = game.player;
  $("#season-value").textContent = player?.season || "—";
  $("#team-value").textContent = player?.team || "—";
  $("#player-value").textContent = player?.name || "—";
  $("#player-card").classList.toggle("hidden", !player);
  if (player) {
    $("#player-context").textContent = `${player.season} · ${player.team}`;
    $("#player-name").textContent = player.name;
    $("#jersey").textContent = `#${player.jersey}`;
    $("#jersey").style.setProperty("--team-primary", player.team_colors.primary);
    $("#jersey").style.setProperty("--team-secondary", player.team_colors.secondary);
    $("#stats").innerHTML = Object.entries(player.stats)
      .map(([label, value]) => `<div><strong>${value}</strong><span>${label}</span></div>`).join("");
    $("#awards").innerHTML = player.awards.length
      ? player.awards.map(award => `<div class="award-badge"><span>${award.icon}</span><strong>${award.label}</strong></div>`).join("")
      : `<p class="no-awards">No qualifying accolades</p>`;
  }

  const grouped = game.categories.reduce((groups, item) => {
    (groups[item.section] ||= []).push(item);
    return groups;
  }, {});
  $("#scorecard").innerHTML = ["Stats", "Accolades", "Joker"].map(section => `
    <section class="score-section"><h3>${section}</h3>${(grouped[section] || []).map(categoryRow).join("")}</section>
  `).join("");

  $$(".category:not(:disabled)").forEach(button => button.addEventListener("click", () => score(button.dataset.category)));
  $$(".slot").forEach(button => {
    button.disabled = !player || game.rerolls_left === 0 || state.busy;
    button.classList.toggle("kept", state.keeps.has(button.dataset.keep));
    button.querySelector(".keep-text").textContent = state.keeps.has(button.dataset.keep) ? "Kept" : "Keep";
  });
  const allKept = state.keeps.size === 3;
  $("#spin").disabled = state.busy || game.complete || (player && (game.rerolls_left === 0 || allKept));
  $("#spin").textContent = player ? (game.rerolls_left ? "Reroll Unkept" : "Choose a Category") : "Spin";

  if (game.complete) {
    $("#final-score").textContent = game.total_score;
    $("#finished").showModal();
  }
}

async function spin() {
  if (state.busy) return;
  setBusy(true);
  try {
    const game = await request("/api/spin", { keeps: [...state.keeps] });
    $("#message").textContent = "";
    setBusy(false);
    render(game);
  } catch (error) {
    $("#message").textContent = error.message;
    setBusy(false);
  }
}

async function score(category) {
  if (state.busy) return;
  setBusy(true);
  try {
    const game = await request("/api/score", { category });
    state.keeps.clear();
    setBusy(false);
    render(game);
  } catch (error) {
    $("#message").textContent = error.message;
    setBusy(false);
  }
}

async function newGame() {
  setBusy(true);
  try {
    const game = await request("/api/new", {});
    state.keeps.clear();
    $("#finished").close();
    setBusy(false);
    render(game);
  } catch (error) {
    $("#message").textContent = error.message;
    setBusy(false);
  }
}

function setBusy(value) {
  state.busy = value;
  document.body.classList.toggle("busy", value);
}

$$('.slot').forEach(button => button.addEventListener('click', () => {
  const keep = button.dataset.keep;
  state.keeps.has(keep) ? state.keeps.delete(keep) : state.keeps.add(keep);
  render(state.game);
}));
$("#spin").addEventListener("click", spin);
$("#new-game").addEventListener("click", newGame);
$("#play-again").addEventListener("click", newGame);

request("/api/state").then(render).catch(error => { $("#message").textContent = error.message; });
