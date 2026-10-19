# Sheet Metal PC Case assembly notes

SPDX-License-Identifier: CERN-OHL-P-2.0

**This is an unprototyped engineering kit, not a certified fabrication package, tested product or load-rated enclosure.** Complete the mandatory process coupons, physical rear-interface gauge and selected-component fit checks before cutting a full case. The physical qualification requirements below must be met at the relevant stages of fabrication and before use.

## 1. Controlling geometry and intentional changes

All dimensions are mm. Front is −Y, rear +Y, up +Z, motherboard component side +X. The approved native baseline is included in `Source/Approved-design.FCStd`; do not rerun historical patch scripts.

| Item | Final nominal geometry |
|---|---|
| Main sled footprint / height | 302 W × 410 D × 520 H; upper outside width 290 |
| Overall including ordinary heads / PCI rail | **306.8 W × 422 D × 520 H**, bounds X−153.4…153.4, Y−205…217, Z0…520 |
| Difference from provisional overall width 304.6 | +2.2 total: ordinary 2.4-high M3 pan heads replace illustrative 1.3-high heads; side planes did not move |
| Sides | 1.5 mm 5052-H32; Ri2.25, K.40; opposed 26.565051° bends, nominal outer virtual Z144/156 and 6 mm joggle |
| Single charcoal wrap | 1 mm steel; Ri1, K.42; opposed 18.434949° front joggle plus floor/roof 90° bends; front outer Y−203/−199, floor Z25, roof Z458 |
| Wrap edge transition | Lower width 298, upper 286. Width tapers only on the straight inclined web between true bend tangencies. The first joggle bend is 298 wide and the second is 286. No projected or open corner-relief approximation |
| Side fastenings | Per side: Y−165/0/165 at Z448; Y−165/+165 at Z11. Ten downward-folded wrap ears; upper ears below roof |
| Capsule grille | Original 546 Ø3.5 bores per side retained;5 mm staggered pitch,1.5 mm nominal minimum web, approximately 5 mm solid bands |
| Visible front capsule | Unchanged 42 × 164 opening. Hidden 46 × 168 fascia,1 mm aluminium, visible plane Y−197.5 |
| Default front I/O | TwoC, twoA, stereo audio and power; completed I03 common concealed mounting plate and commercial header-adapter wiring. See IO-ASSEMBLY.md |
| SSD relocation | Body now Y60…129.85, Z200…300, X−124.5…−117.5: moved 104.065 rearward from the approval envelope to clear standoff L and its new securing nut |
| Optional side fan | Frame moved 3.5 mm inboard to X115…140; mounted by removable F01 bridge, not floating |
| GPU support | Optional 3 mm steel post/ledge, post X116.5…119.5; foot begins X96; adjustable Y/Z and padded ledge below GPU |

The approved silhouette, handle cutouts, grille rings, component datums and single-wrap architecture are retained. The new ordinary roof/back/floor screws are real assembly details. The fully populated I/O is the default; one-C, power-only and blank faces are mutually exclusive alternatives.

## 2. Datums that must stay fixed

PCB Z125…429.8; A=(Y189.7318,Z141.51), **not 146.51**. PCB rear Y199.8918; rear inner Y202; gap 2.1082. PCB underside X−106.975, top X−105.375; tray component face X−116.5; standoff 9.525. All 12 corrected mounting positions are verified in `component-clearances.json`; install only those matching the actual board. Historical B, and microATX R/S, are not installed beneath the depicted ATX board.

Rear I/O X−109.2102…−64.7602, Z273.4884…432.2384:44.45 × 158.75, corner R.8,1 mm shield-interface gauge. Preserve ATX's 2.54 clear band both faces and mask coating there. ATX source opening tolerance ±.2032 and datum-chain tolerances are not replaced by a blanket shop tolerance.

PCI slot pitch 20.32 is retained. The nutstrip is X−1.7677…1.2323, Y203…217 and 3 mm thick; it never crosses the rear wall. Outer retention face remains X2.2323. The seven retention axes follow the source: Z147.4841+n20.32, Y206.1148. They are NOT the aperture centres Z139.1656+n20.32. Two separate nutstrip attachment axes are Y214, Z130/272, clear of the retention washers. The adjacent rear clearance slit is X1…4.2, Z124…277, allowing ordinary Ø7 M3 washers without changing the seven aperture datums. The original bracket-relief profiles in M02 are retained. **A real bracket/cover/GPU interface gauge is mandatory.** The Protocase/ATX setback chains differ 0.4572 mm, and neither advertising envelopes nor this nominal cage establish universal modern GPU bracket fit. If the gauge fails, revise the rear/rail/tray tip-pocket set together before full cutting.

## 3. Cut files, bend interpretation and shop sequence

`DXF/` contains 18 main sheet designs, quantity 19 pieces including two opposite-handed sleds. Ancillary cuts add 10 nominal 0.2 conductive head shims and one 0.5 fascia gasket. Alternatives contain one-C, power-only and fully blank replacement fascias; use one face per case, with the corresponding I/O hardware quantities. Six process coupons remain. There are 29 DXFs total. Obsolete sample-only USB templates have been removed.

Every DXF is cut-only in mm, closed, nonduplicate and without bend/construction entities. Do not scale a drawing or use a perspective projection as a blank. Laser kerf compensation belongs to the shop. `panels.json` gives raw flat local coordinates and the DXF-origin shift; `drawing-geometry.json` gives exact serialized line/arc/circle geometry, normalized to the lower-left blank bounding box. Subtract the stated origin from raw bend-axis coordinates when laying them over a DXF. `supplemental-blanks.json` controls ancillary/alternative/coupon quantities and materials.

The analytical model uses real tangent setbacks and neutral BA=abs(angleRadians)×(Ri+K×t). Constant-gauge CAD geometry is not an experimentally calibrated neutral-axis model: the small expected volume difference between the constant-gauge formed solid and K-developed blank is explicitly checked, not suppressed. `development-check.json` records that correction and residual. K, actual inside radii and springback are **provisional shop assumptions**.

1. Cut/process coupons in the actual material, rolling direction, tooling and finish. Verify R/K/springback and both joggle offsets. Use suitable segmented tooling/fingers for integral ears; confirm forming-tool access before cutting the 1238.0503-long wrap blank.
2. Deburr every cut, particularly handles, grille webs, cable exits and PCI pockets. No sharp burrs inside a cable route. Preserve shield contact bands.
3. Sleds: same 410 × 521.226384 cut blank, opposite fold hands; two opposed bends. Keep outside lower/upper planes at ±151/±145. Do not form two identical hands.
4. Wrap: preform the ten side ears DOWN; form the two front-joggle bends next; floor 90° then roof 90° last, subject to actual brake/tool accessibility. `suggested_forming_step` distinguishes this order from path-order bend numbering.
5. Tray: two 90° channel bends. Two local upper-flange edge reliefs clear the downward left wrap ears. All standoff holes remain simple clearance holes, not structural taps in 1 mm steel.
6. Form C/T clips, carrier and optional fan bridge at Ri1/K.42. Form 3 mm GPU support parts at Ri3/K.40. M02's existing genuinely radiused 1 mm interface is retained; its two end-return segments can share a bend line with suitable tooling.
7. Tap all nine M03 holes M3 × 0.5 through 3 mm after cutting; deburr and gauge. Do not tap the 1 mm rail as the retaining structure.
8. Use two ordinary M3 × 10 pan screws through the front at X68/132, Z336 to secure the concealed carrier. Two small black external heads replace welding; no weld studs or structural adhesive are required.
9. Apply finish with masked grounding/contact regions. Recheck finished Ø5 insert pilots and the exact switch cutout. Protect small grille webs from handling damage.

## 4. Assembly and service

The complete fastener pairs, stacks, nominal engagement and access are in `joint-schedule.json`/CSV. `hardware-bom.csv` aggregates hardware; `hardware-bom-detail.json` retains instance intent. Native fasteners are simplified nominal envelopes with no thread helices, not OEM CAD.

### Chassis and sides

Install four C clips between back and wrap with through-M3 screws/washers/nuts. Attach tray top/bottom flanges to wrap with four M3 joints and connect its rear with two T clips. The clips connect the plates to the chassis. Plain nuts remain accessible with the sides open; their service requirement is intentional.

Fit RRE03-1 inserts in the ten fixed 1 mm wrap ears, not through the removable sides. Supplier basis: finished pilot Ø5, body Ø4.9, reduced head Ø6 × .5,1 mm grip within 0.5–2 range, unset length 9 including head. The CAD depicts the published **unset envelope**; installed bulb shape, mandrel travel, setting force and nose envelope are unknown and must be qualified. Leave setter access open before chassis assembly.

Fixed flange outer planes are ±142.8 upper and ±148.8 lower, giving 0.7 to the unchanged side inner planes. The .5 insert head plus nominal .2 shim fills that gap. Do not pull the side inward to hide a bad coated stack. Tune shim thickness to the measured finished stack while preserving side outer planes. M3 × 8 pan screws provide nominal 4.8 useful engagement past the 1 mm grip region. Test repeated removal, spin resistance and seating.

### Motherboard tray and SSD

Use 9.525 female-M3/male-M3 × 5 standoffs, locknuts behind tray, and M3 × 6 board screws. The reference now has a connected solid base and 6 mm blind female bore; require at least 4.4 mm usable female engagement from the actual supplier. Only install the selected board's actual mounting subset. Do not use unsupported tapped holes in the 1 mm tray. Install standoffs/SSD before board; verify no unused standoff can short a PCB.

SSD bottom screws are M3 × 4 through 1 mm tray, giving nominal 3 mm drive penetration; this is **not universal SSD permission**. Four centers Y64.065/125.785, Z286/209.4:61.72 × 76.6 rectangle, rows 14/90.6 from connector-end body plane Z300. Body spans 69.85 nominal acrossY and 100 alongZ. The inferred 4.065 edge offset and actual drive boss seating need a sample. Reserve the cable-side region above Z300 toward Z335 for SATA connectors;19 mm nominal to left side. Route SATA leads without sharp folding or squeezing against the side; actual plug envelopes remain a gate.

To service the tray, isolate power and remove the necessary sides. Unplug rear and internal leads, then remove the GPU and its support or clamp as needed. Release the rear I/O shield and cables, the two T connections and the four flange bolts. Move sufficiently forward to disengage the rear interface, then extract through the open side. This sequence is a manual access plan, not a verified automated assembly-sweep simulation. Do not force a fully connected board assembly sideways.

### PSU and fans

Four Ø8 × 8 blind-M3 support bosses at X−45/+85,Y95/190, top Z34, bolt from below with M3 × 6. Their contact is digitally verified for all 140/160/180 depths. A nominal 6 deep blind bore leaves 2 mm top wall; screw engages 5 after the 1 mm floor. No PSU modification.

Rear #6-32 pattern is handed from the Intel external AC-face view: global X=95−drawingX, Z=34+drawingY. Global pairs are (−49,114),(89,114),(89,50),(−25,40). The depicted #6-32 × 1/4 screws give 5.35 nominal penetration through the back; check the actual PSU allowed length. Do not flip the PSU and assume this asymmetric pattern still applies. Retain 180 depth plus 60 front cable reserve.

Bottom 140 uses four M4 × 35 through bolts. Rear 140 uses **M4 × 30**, plain nuts and .8 washers:1 back+25 fan+.8 washer+3.2 nut=30, nominal flush full-nut engagement. Check actual stack and use appropriate removable thread locking; do not substitute thick nylocs. M4 × 35 rear screws clash with the optional side bridge. Alternate 120 patterns remain in the floor/rear sheets but are not extra installed fans.

Optional 120: install four M4 × 35 into F01 on the bench, then attach the whole bracket to the roof with two M3 joints. Fan pitch 105, frame X115…140; bracket X114…115. Ordinary 3 mm heads end X143,0.5 from side inner face 143.5 before finish. Cooler tip to frame 42.375, to bracket 41.375; fan-frame rear gap 7. Remove roof connections to service the complete module rather than trying to hold hidden nuts through a spinning fan. Isolate power first.

### PCI and GPU support

Fit M03 behind M02 with two end M3 × 5 screws. Use ordinary M3 washers over bracket notches and M3 × 6 retention screws into 3 mm strip. The seven purchased standard full-height PCI covers are listed in the BOM, not modeled as fake rectangles; substitute the real card bracket for occupied positions. The model's washers reserve a nominal 1 mm bracket/cover layer, so that layer is intentionally absent in CAD. Buy the actual covers and check them and the card against the rear cage using a physical gauge.

G01 bolts through a continuous 54 long floor slot with two M4 × 10 joints. It begins X96,6 clear of the bottom fan's X90 limit. G02 clamps through two vertical slots with M4 × 12. Its top Z193 plus 2 mm nonconductive pad meets nominal GPU underside Z195. SetY and height to an actual stiff, nonfan card surface; do not press on a fan, PCB component or unsupported plastic shroud. The ledge remains below the 35 mm connector reserve. This is an optional untested support, not a lifting/shipping restraint or rated cantilever. If the selected card cannot be supported there, use its maker's support and recheck envelopes.

## 5. Completed front I/O

Follow **IO-ASSEMBLY.md** and the guide's completed I/O sections for mounting, connection topology, cable restraint and variants. The default face has 2C/2A/stereo audio/power at the original centres. I03 is a common 1 mm steel mounting plate behind I02, with four carrier fixings and eight module fixings; its R4.5 edge scallops clear existing carrier joints. No added shell holes, welding or visible fascia screws.

Selected C: Newnex U4S5C01C08-010 through one Delock 67234 per supported Type-E host. Selected A: Newnex USR2-AA-1M through Delock 82941 to one 19-pin two-port host header. Audio: FRONTX P0902_036 stereo rear-output pass-through, not HD_AUDIO/headset/amp. Power PV0F24011 is unchanged:Ø12.1 aperture,14 bezel,9 actuator,M12 × .75,18±1 under-bezel terminal depth; supplied nut/O-ring and insulated PWR_SW leads. Install power/audio on the removed face before closing the carrier, maintaining nut/tool access.

This is a commercial passive extension/header-adapter architecture, not a direct harness or USB-IF-certified chain. Standard 5 V host only; no PD/AltMode/USB4/Thunderbolt claim. Two C require two independent supported Type-E connections. Use the one-C face if only one is available; no Y or legacy-A-to-C-socket adapter, and never an A-male/A-male cable. Qualify the whole connected chain, both C orientations, current and hotplug.

Designer access openings: C14 × 8R2, A20 × 12R1. C nose recess 1.3 is derived from its published 3.2 projection. A4.5 is a reserve recess because forward projection is unpublished, not an OEM-exact datum. Actual C hoods≤12.2 × 6.4 and A≤18 × 10 are nominal access limits; qualify finished corners and shoulders. Simplified modules are declared allocations, not exact supplier models.

Use specified ISO 7380 button heads, not taller pan heads. Nominal head gaps 0.35 to fascia and 0.85 to wrap need coating/flatness checks. Eight M3 × 4 module screws give 2.5 nominal engagement after 1 mm plate+.5 washers; embedded-nut depth is unpublished, so check bottoming and clamp. Maintain flange front Y−193 if factory screws/spacers are substituted.

Audio uses supplier Ø6.1 cutout and supplied nut; finished panel must be strictly<1.2. Pass a hood≤11 through bare deburred rearØ12 before fitting the split nominal ID9 grommet around the cable. Do not assume a plug fits through ID9. Routing constructions allocate R50/Ø10 USB bends and service loops, cushioned restraint and a protected audio lane; they are not supplier minimum-bend/OD specifications. Actual board-dependent tails must be supported clear of fans and must not lever the headers. All physical fit and electrical prototype tests remain mandatory. These are qualification steps, not requests for missing design inputs.

## 6. Bonding, handling and prototype gates

Provide the dedicated M4 chassis bonding point at X130,Z250 on the back. Use an appropriate ring lug/toothed contact stack on a masked metal area; final lug thickness and screw engagement need the actual part. Keep protective-earth arrangements of the certified PSU intact. Never open, drill or modify the PSU or improvise mains wiring.

Mask conductive contact annuli at selected side fasteners/shims, rear-to-wrap clips and tray joints; protect exposed contacts against compatible corrosion. A possible conductive path through hardware is **not measured protective-earth continuity**. Powder coating is insulating. Test chassis, both removable sleds, tray and carrier continuity with the actual finish; add short serviceable bonding braids to appropriate masked stud/lug points if required by the applicable electrical-safety review. Do not rely on anodized/painted contact or assume an insert automatically bonds. Keep braids clear of fans and leave disconnect access. No EMI/ESD or mains safety compliance claim is made.

Handles remain **UNRATED**. Deburr and use only for empty-case handling until a controlled proof/load programme establishes a limit; do not carry a populated case or use it as a shipping handle. No structural FEA, physical prototype, thermal/airflow, vibration, fatigue, acoustic, EMI, electrical-safety or coating durability validation was performed.

The mandatory qualification steps for a full build cover bend/joggle/tool-access coupons; insert setting/head stack/removal; bolted carrier stack; rear I/O and real PCI/card gauge; actual PSU screw intrusion and support seating; motherboard/cooler/RAM; SSD screw/cable fit; selected fan fastener thickness and head clearance; GPU support contact/stiffness; actual I/O modules/adjacent plugs/header count/cable reach; grommet/strain relief; bonding continuity and loaded thermal tests. Changes from those gates require updating native, flats and schedules together.

## 7. Digital check results and limits

Native and coloured STEP: **287 solid-bearing leaf objects,290 solids**, valid; same summed volume **10,045,657.470 mm³** and identical bounds/size above. The three fan references each contain frame/rotor sub-solids; those 3 extra solids are intentional retail-envelope compounds. No STL was requested, and no STL validation is claimed.

All 19 main manufactured sheet instances are valid single solids. Eighteen unique main flat designs pass exact analytic constant-gauge/neutral-development checks; maximum residual 7.794665179972071e−8 mm³ after the stated K correction.

All 2333 circular cuts across the 18 unique designs map back to actual assembled cylinder axes and serialized DXF coordinates; maximum coordinate mismatch 4.95055019201e-09 mm. The opposite sled adds the mirrored 551 circular cuts. Handles/outer profiles originate from the approved native solid, not screenshots.

**29 serialized DXFs;2408 closed loops; zero open nodes or duplicate cut entities.** Maximum readback area error 1.5179975889623165e−6 mm². These are actual saved-file readbacks.

No positive-volume manufactured/main-manufactured interference. Nine expected screw-major-diameter vs M03 tap-drill overlaps are retained in `assembly-check.json` as explicit thread representations, not silently waived geometry errors. Eight reference-envelope overlaps are the four SSD and four PSU screw intrusions into undrilled component boxes; allowed penetration remains a physical gate. The earlier tray/ear andSSD/standoff clashes were corrected and rechecked.

All 12 corrected board positions, all three PSU depths and the modeled 35 GPU/60 PSU reserves pass their digital checks. Real connector, motherboard detail, bracket, tool and cable shapes are not established by boxes.

The new I/O hardware has zero unexpected clashes. Ten continuous routing allocations were checked against solids; USB clearance minimum 3 mm and audio about 2.994 mm. Unplaced header tails and unknown supplier bend limits are not certified. Portable source and idempotent subsystem regeneration passed. See the machine-readable validation files for exact results. A valid export is not physical fit or manufacturing certification.
