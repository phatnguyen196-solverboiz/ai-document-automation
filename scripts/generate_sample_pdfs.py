from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "sample_documents"

SAMPLES = {
    "01-valid-shipping-order.pdf": [
        "SHIPPING ORDER",
        "Customer: ABC Electronics",
        "Container Number: TCLU1234567",
        "Origin: Ho Chi Minh City",
        "Destination: Singapore",
        "Weight: 840 kg",
        "Delivery Date: 2026-09-25",
    ],
    "02-missing-container-number.pdf": [
        "SHIPPING ORDER",
        "Customer: Mekong Textiles",
        "Origin: Can Tho",
        "Destination: Bangkok",
        "Weight: 1250 kg",
        "Delivery Date: 2026-10-02",
    ],
    "03-invalid-weight.pdf": [
        "SHIPPING ORDER",
        "Customer: Lotus Furniture",
        "Container Number: MSCU7654321",
        "Origin: Da Nang",
        "Destination: Manila",
        "Weight: -25 kg",
        "Delivery Date: 2026-10-08",
    ],
    "04-missing-destination.pdf": [
        "SHIPPING ORDER",
        "Customer: Saigon Coffee Export",
        "Container Number: CMAU2468135",
        "Origin: Ho Chi Minh City",
        "Weight: 2200 kg",
        "Delivery Date: 2026-10-12",
    ],
    "05-alternate-date-format.pdf": [
        "SHIPPING ORDER",
        "Customer: Pacific Components",
        "Container Number: OOLU1357924",
        "Origin: Hai Phong",
        "Destination: Singapore",
        "Weight: 1850 lbs",
        "Delivery Date: 18 October 2026",
    ],
}


def create_pdf(path: Path, lines: list[str]) -> None:
    pdf = fitz.open()
    page = pdf.new_page(width=595, height=842)
    page.draw_rect(fitz.Rect(48, 48, 547, 794), color=(0.1, 0.3, 0.28), width=1)
    page.insert_text((76, 100), lines[0], fontsize=22, fontname="helv", color=(0.07, 0.25, 0.23))
    page.insert_text((76, 128), "FreightMind deterministic demo document", fontsize=10, color=(0.4, 0.48, 0.46))
    y = 185
    for line in lines[1:]:
        page.insert_text((76, y), line, fontsize=13, fontname="helv", color=(0.12, 0.2, 0.2))
        y += 42
    page.insert_text((76, 750), "Generated for local portfolio demonstration only.", fontsize=9, color=(0.45, 0.5, 0.49))
    pdf.save(path)
    pdf.close()


if __name__ == "__main__":
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for filename, content in SAMPLES.items():
        create_pdf(OUTPUT / filename, content)
    print(f"Generated {len(SAMPLES)} sample PDFs in {OUTPUT}")
