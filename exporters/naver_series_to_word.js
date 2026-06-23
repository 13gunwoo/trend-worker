// exporters/naver_series_to_word.js
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
function heading1(text) {
    return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text, font: "Arial", size: 32, bold: true })] });
}
function heading2(text) {
    return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text, font: "Arial", size: 28, bold: true })] });
}
function spacer() { return new Paragraph({ children: [new TextRun("")] }); }

function rankingTable(items) {
    const colWidths = [600, 700, 2000, 1200, 1200, 800, 600, 1000, 800];
    const headers = ["순위", "변동", "제목", "작가", "출판사", "총화수", "별점", "다운로드", "댓글"];
    const totalWidth = colWidths.reduce((a, b) => a + b, 0);
    const rows = [new TableRow({ children: headers.map((h, i) => headerCell(h, colWidths[i])) })];
    for (const item of items) {
        rows.push(new TableRow({ children: [
            dataCell(item["순위"],        colWidths[0]),
            dataCell(item["변동"] || "", colWidths[1]),
            dataCell(item["제목"],        colWidths[2]),
            dataCell(item["작가"],        colWidths[3]),
            dataCell(item["출판사"],      colWidths[4]),
            dataCell(item["총화수"],      colWidths[5]),
            dataCell(item["별점"],        colWidths[6]),
            dataCell(item["전체다운로드수"], colWidths[7]),
            dataCell(item["전체댓글수"],  colWidths[8]),
        ]}));
    }
    return new Table({ width: { size: totalWidth, type: WidthType.DXA }, columnWidths: colWidths, rows });
}

const children = [];
children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: platform + " 트렌드 리포트 (" + today + ")", bold: true, font: "Arial", size: 40 })]
}));
children.push(spacer());

const rankingData = data["랭킹데이터"] || {};
for (const [periodKo, categories] of Object.entries(rankingData)) {
    children.push(heading1(periodKo));
    for (const [categoryKo, items] of Object.entries(categories)) {
        if (items && items.length > 0) {
            children.push(heading2(categoryKo));
            children.push(rankingTable(items));
            children.push(spacer());
        }
    }
}

const doc = new Document({
    styles: {
        default: { document: { run: { font: "Arial", size: 20 } } },
        paragraphStyles: [
            { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 32, bold: true, font: "Arial", color: "2E75B6" },
              paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 } },
            { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 28, bold: true, font: "Arial", color: "2E75B6" },
              paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 1 } },
        ]
    },
    sections: [{ properties: { page: { size: { width: 16838, height: 11906 }, margin: { top: 1000, right: 1000, bottom: 1000, left: 1000 } } }, children }]
});

Packer.toBuffer(doc).then(buffer => { fs.writeFileSync(filepath, buffer); console.log(filepath); });
