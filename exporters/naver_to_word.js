// exporters/naver_to_word.js
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
    const colWidths = [600, 2400, 1200, 800, 2000];
    const headers = ["순위", "제목", "작가", "순위상승", "URL"];
    const rows = [new TableRow({ children: headers.map((h, i) => headerCell(h, colWidths[i])) })];
    for (const item of items) {
        rows.push(new TableRow({ children: [
            dataCell(item["rank"], colWidths[0]),
            dataCell(item["title"], colWidths[1]),
            dataCell(item["author"], colWidths[2]),
            dataCell(item["isUp"] ? "↑" : "", colWidths[3]),
            dataCell(item["url"], colWidths[4]),
        ]}));
    }
    const totalWidth = colWidths.reduce((a, b) => a + b, 0);
    return new Table({ width: { size: totalWidth, type: WidthType.DXA }, columnWidths: colWidths, rows });
}

function listTable(items) {
    const colWidths = [600, 2400, 1200, 600, 2000];
    const headers = ["순위", "제목", "작가", "별점", "URL"];
    const rows = [new TableRow({ children: headers.map((h, i) => headerCell(h, colWidths[i])) })];
    for (const item of items) {
        rows.push(new TableRow({ children: [
            dataCell(item["rank"], colWidths[0]),
            dataCell(item["title"], colWidths[1]),
            dataCell(item["author"], colWidths[2]),
            dataCell(item["starScore"] || "", colWidths[3]),
            dataCell(item["url"], colWidths[4]),
        ]}));
    }
    const totalWidth = colWidths.reduce((a, b) => a + b, 0);
    return new Table({ width: { size: totalWidth, type: WidthType.DXA }, columnWidths: colWidths, rows });
}

function trendTagTable(tags) {
    const colWidths = [3000, 1000];
    const rows = [new TableRow({ children: [headerCell("태그", colWidths[0]), headerCell("빈도수", colWidths[1])] })];
    for (const t of tags) {
        rows.push(new TableRow({ children: [
            dataCell(t["tag"], colWidths[0]),
            dataCell(t["count"], colWidths[1]),
        ]}));
    }
    const totalWidth = colWidths.reduce((a, b) => a + b, 0);
    return new Table({ width: { size: totalWidth, type: WidthType.DXA }, columnWidths: colWidths, rows });
}

function popularTable(items) {
    const colWidths = [2000, 1000, 2000, 2000];
    const headers = ["제목", "구독자수", "태그", "URL"];
    const rows = [new TableRow({ children: headers.map((h, i) => headerCell(h, colWidths[i])) })];
    for (const item of items) {
        rows.push(new TableRow({ children: [
            dataCell(item["title"], colWidths[0]),
            dataCell(item["favoriteCount"], colWidths[1]),
            dataCell((item["tags"] || []).join(", "), colWidths[2]),
            dataCell(item["url"], colWidths[3]),
        ]}));
    }
    const totalWidth = colWidths.reduce((a, b) => a + b, 0);
    return new Table({ width: { size: totalWidth, type: WidthType.DXA }, columnWidths: colWidths, rows });
}

const children = [];
children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: platform + " 트렌드 리포트 (" + today + ")", bold: true, font: "Arial", size: 40 })]
}));
children.push(spacer());

// 랭킹
if (data["랭킹"]) {
    children.push(heading1("랭킹"));
    for (const [label, items] of Object.entries(data["랭킹"])) {
        if (items && items.length > 0) {
            children.push(heading2(label + " 랭킹"));
            children.push(rankingTable(items));
            children.push(spacer());
        }
    }
}

// 요일별 랭킹
if (data["요일별랭킹"]) {
    children.push(heading1("요일별 랭킹"));
    for (const [day, items] of Object.entries(data["요일별랭킹"])) {
        if (items && items.length > 0) {
            children.push(heading2(day + "요일"));
            children.push(listTable(items));
            children.push(spacer());
        }
    }
}

// 장르별 랭킹
if (data["장르별랭킹"]) {
    children.push(heading1("장르별 랭킹"));
    for (const [genre, items] of Object.entries(data["장르별랭킹"])) {
        if (items && items.length > 0) {
            children.push(heading2(genre));
            children.push(listTable(items));
            children.push(spacer());
        }
    }
}

// 검색결과
if (data["검색결과"]) {
    const query = data["검색결과"]["검색어"] || "";
    const items = data["검색결과"]["목록"] || [];
    if (items.length > 0) {
        children.push(heading1("검색결과: " + query));
        children.push(listTable(items));
        children.push(spacer());
    }
}

// 트렌드 분석
if (data["트렌드분석"]) {
    children.push(heading1("트렌드 분석"));
    const tags = data["트렌드분석"]["트렌드태그"] || [];
    if (tags.length > 0) {
        children.push(heading2("트렌드 태그 TOP 20"));
        children.push(trendTagTable(tags));
        children.push(spacer());
    }
    const popular = data["트렌드분석"]["인기작"] || [];
    if (popular.length > 0) {
        children.push(heading2("구독자수 기준 인기작 TOP 20"));
        children.push(popularTable(popular));
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
            { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 28, bold: true, font: "Arial", color: "2E75B6" },
              paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 1 } },
        ]
    },
    sections: [{ properties: { page: { size: { width: 16838, height: 11906 }, margin: { top: 1000, right: 1000, bottom: 1000, left: 1000 } } }, children }]
});

Packer.toBuffer(doc).then(buffer => { fs.writeFileSync(filepath, buffer); console.log(filepath); });
