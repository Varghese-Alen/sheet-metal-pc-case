# Sheet Metal PC Case front I/O assembly

**Unprototyped engineering design, not a certified cable chain or verified OEM fit.** The default I01 now has two USB-C, two USB-A, stereo audio and the unchanged power switch. Shell, port centres, motherboard/PCI datums and unrelated panels are unchanged. I03 is one common concealed steel plate, not four independent crossbars. See `io-interfaces.json` for machine-readable dimensions and variants.

## Selected electrical architecture

| Quantity, full version | Selected item | Connection / qualification |
|---|---|---|
| 2 | Newnex **U4S5C01C08-010**, 1 m panel-C female → C male | Each male plugs into its own Delock 67234; each adapter requires an independent supported motherboard/controller Type-E port. Drawing includes CC, VCONN and all four SuperSpeed pairs. |
| 2 | Delock **67234**, Type-E Key A 20-pin male → C female | Approx. 18 × 15 × 7 mm. Combined adapter/male-hood service allocation 55 × 20 × 15 mm. These are not installed board-header coordinates. Support the cable near the actual header; never lever the header with cable weight. |
| 2 | Newnex **USR2-AA-1M**, panel-A female → A male | Catalogue links the USR2-A family drawing. Receiving variant must match the specified flange and mounting pitch. Each male connects to one female on 82941. **Never use an A-male/A-male cable.** |
| 1 | Delock **82941**, 19-pin female header → two A females, **45 cm including connectors** | Uses one supported two-port 19-pin host header. Secure the two added mated pairs in the cushioned, laced cradle; no dangling couplers. Its outline is an allocation, not full OEM CAD. |
| 1 | FRONTX **P0902_036 / P0902-036**, **36 in / 914.4 mm** | Stereo 3.5 mm female → male rear-output pass-through, **not HD_AUDIO, headset microphone or an amplifier**. Route externally from the protected rear exit to the selected board's stereo output. |
| 1 | E-Switch **PV0F24011** | Existing geometry and Ø12.1 aperture unchanged. Momentary motherboard PWR_SW connection; insulate terminals. Not a mains switch. |

The USB implementation is a **commercial passive extension/header-adapter architecture**, not a direct internal harness and not a USB-IF-certified cable chain. No Y adapters or legacy-A-to-C-socket adapters. Standard **5 V host operation only**; no PD, Alt Mode, USB4 or Thunderbolt claim. Component ratings do not establish whole-chain speed: test enumeration, throughput, hot-plug and both C plug orientations with the actual host and cables. Respect the host's current budget.

**C orientation test matrix, per installed C chain:** rear male-to-67234 at 0° / front plug 0°; rear 0° / front 180°; rear 180° / front 0°; rear 180° / front 180°. Test enumeration, USB2/SuperSpeed operation, throughput and hotplug in all **four local combinations**. If the device end of the external cable is also reversible, repeat with that end reversed (eight combinations total). Confirm standard 5 V operation within the host/component current budget; this does not authorize PD testing or a higher power rating.

## Sheet interfaces and fasteners

All dimensions are in mm.

All centres are at X100: power Z400; C380/360; A337/316; audio Z281.

### I01

I01 is 1.0 aluminium, with its front at Y−197.5 and back at −196.5. Finished thickness at audio must remain **strictly below 1.2**. Mask the supplied nut/body bearing seats and bore so coating does not consume the short thread; retain bare-metal seating under the hardware. C access openings 14 × 8 R2; A 20 × 12 R1; supplier audio hole Ø6.1; power Ø12.1 unchanged. USB openings are **designer plug-access apertures**, not manufacturer-recommended cutouts. Trial plugs must clear the rounded corners: nominal hood allocations C ≤12.2 × 6.4, A ≤18 × 10. The C 12.2 × 6.4 rectangular hood has approximately 0.37 mm nominal corner clearance in the R2 opening; this is not a finished-tolerance guarantee. Larger or locking hoods need a separate fit check.

### I02

I02 is the existing folded carrier. Its front/back planes are Y−195.5/−194.5 and its window is X81..119/Z260..412. The existing shell bolts and returns are retained. Add four Ø3.4 holes at X72/128, Z308/386. Existing tie holes remain; no added shell holes or visible screws.

### I03

I03 is a 1 mm steel flat at X66..134/Z303..391, Y−194.5..−193.5, with a 68 × 88 outline. Top notch X90..110/Z389..391. **Two R4.5 open edge scallops at X68/132, Z336** clear the retained cage bolts, Ø7 washers and nuts by 1 mm nominal. These scallops were added after collision checking. No bends.

Four I03/I02 attachments: **M3 × 6 ISO 7380-1 button heads**, maximum Ø5.7 × 1.65, 0.5 mm washer and plain M3 nut, height 2.4. Stack 1 + 1 + 0.5 + 2.4 = 4.9; nominal tip 1.1. Heads Y−197.15..−195.5 retain **0.85 nominal clearance** to wrap inner Y−198.

Four module flanges seat at **Y−193.0** on **two 0.5 mm M3 flat washers each**, behind I03. C mounting pitch 20 (X90/110), A pitch 30 (X85/115), all plate holes Ø3.4. Use **eight M3 × 4 ISO 7380-1 button heads**, max Ø5.7 × 1.65. The 1 mm plate +0.5 washer leaves **2.5 nominal engagement** in the supplier's embedded M3 nuts. **Permitted thread depth is unpublished:** check screw bottoming, clamp and engagement at receiving. If needed use suitable factory screws/spacers while preserving the Y−193 flange datum. Do not substitute ordinary pan heads with larger height. M3 × 4 button heads are commercially listed, e.g. TR00004815-000.

Module screw fronts at Y−196.15 leave **0.35 nominal clearance** to the fascia back. This small gap requires checks of paint, flatness, washer thickness and actual head tolerances. The 0.35 is not a finish allowance guarantee.

C: published flange 30 × 8, pitch 20, nose projects 3.2; nose plane Y−196.2 means **1.3 recess** from the fascia. Published rear 37.5 includes Ø9.3 relief; end Y−155.5. The published male hood is 35 × 12.2 × 6.4.

A: linked family flange 38.5 × 13.7, pitch 30, nose width 17.8, body 26.5/rear 36.5, end Y−156.5. No forward nose projection is published: allocate zero, giving **4.5 front reserve recess**, **not an OEM-exact setback**.

Audio: body Ø11.5 × 32 plus 15 relief, rear end Y−149.5. Body shoulder seats fascia back; 3 mm exposed threaded length spans 1 mm panel + supplied Ø8 × 1.8 ring nut +0.2 nominal tip. **Use the supplied nut; thread specification is unpublished.** The design therefore does not assign a metric thread specification.

The new module bodies, mouths, internal tongues and adapters are **simplified reference allocations, not OEM models**. Published flange/pitch/overall rear limits control; C body/relief partition, corner profiles, mouth thickness/height and A relief diameter are not manufacturer dimensions. Mouth colours/rounded C silhouette/blue A insulator are illustrative. The model does not validate unpublished internal thread geometry.

## Bench assembly and service

1. Deburr I01/I02/I03, especially cable passages. Trial the actual nuts, screw lengths and plug hoods before coating. Check the finished audio thickness separately.
2. With the carrier removed, fit four I03 attachment bolts through I02 and I03, heads toward the front. Add rear washers and plain nuts. The plate's edge scallops must clear the existing carrier joint hardware; do not move those joints.
3. Fit the four USB modules behind I03 with eight spacer washers and eight button screws. Verify flange datum, no screw bottoming, and actual plug insertion/release through I01. The plate retains an R10 power-tool allocation with 1 mm minimum nominal gap; actual power nut/tool fit remains a receiving check.
4. Fit the audio connector and supplied front nut; retain the power switch. Capture the fascia with the existing 0.5 gasket and four 1 mm rear pads. Refit I02 on the existing two M3 × 10 through-bolts/spacers at X68/132, Z336. No welding and no extra visible fascia screws. For service, unplug leads and remove those two accessible carrier nuts; withdraw the cage/face inward and work on the bench.
5. Connect only the topology above. A board with just one suitable Type-E host uses the C1 fascia variant, not a splitter. Keep header connections unpowered during assembly.

## Cable support and protected routing

Native `IO_Routing_Construction` contains **nonmaterial** centreline, service-loop, restraint and mating-space allocations. They have no manufactured mass and are excluded from the solid STEP. They are not physical cable solids or claims of a completely qualified installed harness.

USB entries leave the published rear relief ends, then turn at **R50** through the front void. Reserve **Ø10** around the continuous paths. R50/Ø10 are designer allocations; actual cable OD and minimum bend radius are unpublished and must be checked.

One OPEN 270° R50 service loop per lead is centred X0/Y−140 at its port Z, with allocated swept bounds X±55/Y−195..−85. Each open loop consumes 235.62 mm and ends at X50/Y−140, leaving a separate tail; it does not cross its own entry. Entry plus one loop leaves approximately 619–620 mm of the raw 1 m end-to-end budget, NOT all flexible cable. Deduct a provisional 85 mm C /90 mm A connector-end allowance, leaving approximately 529–535 mm flexible-tail allocation; verify the actual supplier length datum and hood lengths before routing. Distribute remaining slack in separated supported loops; do not force it into a tight coil. Actual header endpoints are board dependent, not the construction-box positions.

Existing left I02 return holes at X62/Y−181,−177/Z300,380 anchor a **cushioned lacing spine**. Four separate broad straps support the service loops. The two A mated pairs have individual straps and a tethered insulated cradle above the GPU. Use eight 2.5 mm releasable ties and six broad cushioned straps plus abrasion sleeves; adjust tension without crushing data cables. Support each Type-E lead near its actual header, not by loading the PCB socket.

The shown swept routes stay above the GPU and out of CPU/optional-fan hardware; continuous centreline-to-solid distance checks are in `io-clearance-check.json`. Those checks do not qualify the unplaced header tails or unknown vendor bend radii, and they do not replace testing for wires snagging on fans. Keep every finished tail away from fan blades and heatsinks.

Audio follows the right perimeter lane around Z281, below the optional fan, to the unchanged rear exit X130/Z280. Use sleeved strain relief on the existing right return. **Remove the split grommet, pass a plug hood no larger than Ø11 through the bare deburred Ø12 panel hole, then fit the split grommet around the cable.** Nominal grommet ID9 is not proven to pass the plug. Reject larger hoods under this design; do not force them through. Actual cable OD must suit the grommet. Keep the external run protected and strain-relieved to the selected rear stereo-output socket; exact socket position varies by board.

Power retains the existing switch and has a separate insulated pair-entry/support allocation. Continue to the actual motherboard PWR_SW pins; do not connect it to USB power or safety earth.

## Mutually exclusive fascia variants

| DXF / native flat | C / A / audio / power | I03 | 67234 / 82941 | Module M3 × 4 / spacer washers |
|---|---|---:|---|---|
| `I01` (default) | 2 / 2 / 1 / 1 | 1 | 2 / 1 | 8 / 8 |
| `Alternatives/I01-C1` | 1 at 380 / 2 / 1 / 1; lower C blank | 1 | 1 / 1 | 6 / 6 |
| `Alternatives/I01-power-only` | 0 / 0 / 0 / 1 | 0 | 0 / 0 | 0 / 0 |
| `Alternatives/I00-fully-blank-option` | 0 / 0 / 0 / 0 | 0 | 0 / 0 | 0 / 0 |

Use one fascia per case. I02/gasket/pads remain for all variants. Where I03 is used, also supply 4 M3 × 6 screws, 4 washers and 4 plain nuts. Omit USB/audio-only cables, restraints and hardware when those ports are absent. Main BOM is the full version; alternatives are not extra main assembly sheets. Obsolete sample-gated I/O DXFs are removed and are no longer generated.

## Evidence and qualification boundary

The primary sources below are linked, not redistributed.

[Newnex C drawing](https://newnex.com/documents/drawings/U4S5C01C08-010.PDF), rev A 2024-01-15; dimensional bounds and full-feature wire table.

[Newnex catalogue](https://newnex.com/usb-3-panel-mount-cables.php) and [USR2-A family drawing](https://newnex.com/documents/USR2-A-Custom-Drawing.PDF); selected commercial USR2-AA-1M links to this family, not a vendor-certified case fit.

[Delock 67234](https://www.delock.com/produkt/67234/pdf.html?sprache=en), [Delock 82941](https://www.delock.com/produkt/82941/pdf.html?sprache=en). Direct downloads were bot-challenged; manufacturer-indexed listing/datasheet information was used, not invented adapter CAD.

[FRONTX P0902_036](https://www.frontx.com/pro/p0902_036.html), explicitly 3 ft, and [dimensions](https://www.frontx.com/pro/3.5audio_dimensions.gif).

[Commercial M3 × 4 button screw](https://www.trfastenings.com/products/catalogue/screws-and-bolts/Hexagon-Socket-Screws/Button-Head/TR00004815-000).

Proprietary supplier PDFs/STEP are research-only and are **not included or relicensed**. Export validity, nominal clearances and developed-hole agreement do not prove physical fit, signal integrity, strength, thermal performance, bonding or safety. Receiving/finished-stack checks and a physical prototype remain mandatory; the documented design and qualification plan can be used without further user-supplied data.
