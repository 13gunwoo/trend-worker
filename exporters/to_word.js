// exporters/to_word.js
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
    const colWidths = [800, 800, 2000, 1200, 1000, 1000, 1000, 800, 1000];
    const headers = ["순위", "변동", "작품명", "작가", "장르", "조회수", "연재상태", "연령등급", "series_id"];
    const totalWidth = colWidths.reduce((a, b) => a + b, 0);
    const rows = [new TableRow({ children: headers.map((h, i) => headerCell(h, colWidths[i])) })];
    for (const item of items) {
        rows.push(new TableRow({ children: [
            dataCell(item["순위"], colWidths[0]), dataCell(item["변동"], colWidths[1]),
            dataCell(item["작품명"], colWidths[2]), dataCell(item["작가"], colWidths[3]),
            dataCell(item["장르"], colWidths[4]), dataCell(item["조회수"], colWidths[5]),
            dataCell(item["연재상태"], colWidths[6]), dataCell(item["연령등급"], colWidths[7]),
            dataCell(item["series_id"], colWidths[8]),
        ]}));
    }
    return new Table({ width: { size: totalWidth, type: WidthType.DXA }, columnWidths: colWidths, rows });
}

function heading1(text) {
    return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text, font: "Arial", size: 32, bold: true })] });
}
function heading2(text) {
    return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text, font: "Arial", size: 28, bold: true })] });
}
function spacer() { return new Paragraph({ children: [new TextRun("")] }); }

const children = [];
children.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: platform + " 트렌드 리포트 (" + today + ")", bold: true, font: "Arial", size: 40 })] }));
children.push(spacer());

if (data["실시간랭킹"]) { children.push(heading1("실시간 랭킹")); children.push(rankingTable(data["실시간랭킹"])); children.push(spacer()); }

if (data["장르별랭킹"]) {
    children.push(heading1("장르별 랭킹"));
    for (const [genre, items] of Object.entries(data["장르별랭킹"])) { children.push(heading2(genre)); children.push(rankingTable(items)); children.push(spacer()); }
}

if (data["신작"]) {
    children.push(heading1("신작"));
    const colWidths = [1200, 2000, 1000, 1000, 800, 1000];
    const headers = ["날짜", "작품명", "장르", "조회수", "연령등급", "series_id"];
    const totalWidth = colWidths.reduce((a, b) => a + b, 0);
    const rows = [new TableRow({ children: headers.map((h, i) => headerCell(h, colWidths[i])) })];
    for (const dayGroup of data["신작"]) {
        for (const item of dayGroup["작품목록"]) {
            rows.push(new TableRow({ children: [
                dataCell(dayGroup["날짜"], colWidths[0]), dataCell(item["작품명"], colWidths[1]),
                dataCell(item["장르"], colWidths[2]), dataCell(item["조회수"], colWidths[3]),
                dataCell(item["연령등급"], colWidths[4]), dataCell(item["series_id"], colWidths[5]),
            ]}));
        }
    }
    children.push(new Table({ width: { size: totalWidth, type: WidthType.DXA }, columnWidths: colWidths, rows }));
    children.push(spacer());
}

if (data["작품상세"] && data["작품상세"].length > 0) {
    children.push(heading1("작품 상세"));
    const colWidths = [900, 1800, 1000, 900, 900, 1000, 1000, 1200];
    const headers = ["series_id", "작품명", "작가", "장르", "연재상태", "조회수", "별점", "결제방식"];
    const totalWidth = colWidths.reduce((a, b) => a + b, 0);
    const rows = [new TableRow({ children: headers.map((h, i) => headerCell(h, colWidths[i])) })];
    for (const item of data["작품상세"]) {
        rows.push(new TableRow({ children: [
            dataCell(item["series_id"], colWidths[0]), dataCell(item["작품명"], colWidths[1]),
            dataCell(item["작가"], colWidths[2]), dataCell(item["장르"], colWidths[3]),
            dataCell(item["연재상태"], colWidths[4]), dataCell(item["조회수"], colWidths[5]),
            dataCell(item["별점"], colWidths[6]), dataCell(item["결제방식"], colWidths[7]),
        ]}));
    }
    children.push(new Table({ width: { size: totalWidth, type: WidthType.DXA }, columnWidths: colWidths, rows }));
    children.push(spacer());
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
