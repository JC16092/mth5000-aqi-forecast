// Generates the six chapter-badge icons used on the Agenda slide and each
// Section Divider slide: a solid coral circle with a white Font Awesome
// icon centered on it, rendered via react-icons -> SVG -> sharp.
// Keep ACCENT in sync with AMBER in build_deck.js -- they're the same
// accent color, just defined in two files since this script only needs
// the one value.
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const path = require("path");
const fa = require("react-icons/fa");

const OUT = path.join(__dirname, "icons");
const SIZE = 600;
const ACCENT = "#E35D45";

const ICONS = {
  introduction: "FaExclamationTriangle",
  literature: "FaBook",
  methodology: "FaCogs",
  results: "FaChartLine",
  discussion: "FaBalanceScale",
  conclusion: "FaFlagCheckered",
};

async function renderBadge(name, iconKey) {
  const Icon = fa[iconKey];
  const iconSize = Math.round(SIZE * 0.52);
  const iconSvg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(Icon, { color: "#FFFFFF" })
  );
  const iconPng = await sharp(Buffer.from(iconSvg)).resize(iconSize, iconSize, { fit: "contain" }).png().toBuffer();

  const circleSvg = `<svg width="${SIZE}" height="${SIZE}" xmlns="http://www.w3.org/2000/svg">
    <circle cx="${SIZE / 2}" cy="${SIZE / 2}" r="${SIZE / 2}" fill="${ACCENT}"/>
  </svg>`;

  await sharp(Buffer.from(circleSvg))
    .composite([{ input: iconPng, gravity: "center" }])
    .png()
    .toFile(path.join(OUT, `${name}.png`));
  console.log("wrote", name);
}

(async () => {
  for (const [name, iconKey] of Object.entries(ICONS)) {
    await renderBadge(name, iconKey);
  }
})();
