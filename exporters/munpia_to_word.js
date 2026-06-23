// exporters/munpia_to_word.js
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType } = require("docx");
const fs = require("fs");
const path = require("path");

const dataPath = process.env.TEMP_DATA_PATH || "/tmp/trend_data.json";
const data = JSON.parse(fs.readFileSync(dataPath, "utf-8"));
const outputDir = process.argv[2] || "/tmp";

const today = new Date().toISOString().slice(0, 10);
const platform = data["플랫폼"] || "unknown";
const filename = platform + "_" + today.replace(/-/g, "") + ".docx";
const filepath = path.join(outputDir, filename);

const BORDER = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
const HEADER_FILL = { fill: "2E75B6", type: ShadingType.CLEAR };

function headerCell(text, width) {
    return new TableCell({
        borders: BORDERS, width: { size: width, type: WidthType.DXA },
        shading: HEADER_FILL, margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: "FFFFFF", font: "Arial", size: 18 })] })]
    });
}

function dataCell(text, width) {
    return new TableCell({
        borders: BORDERS, width: { size: width, type: WidthType.DXA },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({ children: [new TextRun({ text: String(text || ""), font: "Arial", size: 18 })] })]
    });
}

function rankingTable(items) {
    const colWidths = [600, 2200, 1200, 1000, 2000, 2000];
    const headers = ["순위", "제목", "작가", "장르", "URL", "소개글"];
    const totalWidth = colWidths.reduce((a, b) => a + b, 0);
    const rows = [new TableRow({ children: headers.map((h, i) => headerCell(h, colWidths[i])) })];
    for (const item of items) {
        rows.push(new TableRow({ children: [
            dataCell(item["rank"], colWidths[0]),
            dataCell(item["title"], colWidths[1]),
            dataCell(item["author"], colWidths[2]),
            dataCell(item["genre"], colWidths[3]),
            dataCell(item["url"], colWidths[4]),
            dataCell(item["description"] || "", colWidths[5]),
        ]}));
    }
    return new Table({ width: { size: totalWidth, type: WidthType.DXA }, columnWidths: colWidths, rows });
}

function heading1(text) {
    return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text, font: "Arial", size: 32, bold: true })] });
}
function spacer() { return new Paragraph({ children: [new TextRun("")] }); }

const categoryMap = [
    ["무료투데이베스트", "무료 투데이 베스트"],
    ["유료투데이베스트", "유료 투데이 베스트"],
    ["유료신규베스트",   "유료 신규 베스트"],
    ["유료인기급상승",   "유료 인기급상승 베스트"],
];

const children = [];
children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: platform + " 트렌드 리포트 (" + today + ")", bold: true, font: "Arial", size: 40 })]
}));
children.push(spacer());

for (const [key, label] of categoryMap) {
    if (data[key] && data[key].length > 0) {
        children.push(heading1(label));
        children.push(rankingTable(data[key]));
        children.push(spacer());
    }
}

const doc = new Document({
    styles: {
        default: { document: { run: { font: "Arial", size: 20 } } },
        paragraphStyles: [
            { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 32, bold: true, font: "Arial", color: "2E75B6" },
              paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 } },
        ]
    },
    sections: [{ properties: { page: { size: { width: 16838, height: 11906 }, margin: { top: 1000, right: 1000, bottom: 1000, left: 1000 } } }, children }]
});

Packer.toBuffer(doc).then(buffer => { fs.writeFileSync(filepath, buffer); console.log(filepath); });
