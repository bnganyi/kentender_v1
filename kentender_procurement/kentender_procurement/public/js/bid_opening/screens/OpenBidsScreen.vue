<!-- BOP-DES-02 Open bids (BOP-CHG-001 v0.10 §10.3, §10.7; boards c1–c13b,
     c10–c12, z1, n1, n2), ported class-for-class. What is shown follows the
     server's answer for this viewer: its state, its pause and the next step's
     primary action. Forms the chair or a member opens themselves (a request,
     a comment for Evaluation, a member's own account) are local modes; every
     action is a server command, and the page reloads after each. -->
<template>
	<div class="kt-page" :data-screen="`open-bids:${mode}`">
		<PageHead :title="`Bid opening · ${opening.tender_reference}`" :desc="opening.title" :status="opening.status" />
		<Guidance :answer="answer" :journey="data.journey" :pending="pending" @fix="onFix" />

		<!-- before Start: c1–c3, c2b–c2d -->
		<template v-if="mode === 'pre'">
			<div v-if="problemRow" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="kt-btn kt-btn-secondary" data-testid="bop-view-problem" @click="showProblem = !showProblem">View problem details</button></div>
			<div v-if="serviceIncident" class="kt-region" data-testid="bop-why-not-start"><h2>Why the opening cannot start</h2>
				<div class="kt-meta-row"><div><span class="kt-label">{{ serviceIncident.notification_state === "Delivered" ? "Being handled by" : "Assigned to" }}</span><span class="kt-meta-value">{{ serviceIncident.holder }}</span></div><div><span class="kt-label">Status</span><span class="kt-meta-value">{{ serviceIncident.notification_state === "Delivered" ? `Support notified ${serviceIncident.notified_label}` : "Not yet notified" }}</span></div><div><span class="kt-label">Reference</span><span class="kt-meta-value">{{ serviceIncident.incident_id }}</span></div></div>
				<div v-if="serviceIncident.notification_state === 'Delivered'" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="kt-btn kt-btn-secondary" @click="showProblem = !showProblem">View problem details</button></div>
				<p v-else style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">Notify support resends the notice for the same problem. It does not open a new one.</p>
			</div>
			<CommitteeTable :members="members" :secondary="!!serviceIncident">
				<button v-for="fix in notifyFixes" :key="fix.target" type="button" class="kt-btn kt-btn-secondary" :data-testid="`bop-notify-${fix.target}`" :disabled="pending" @click="onFix(fix)">{{ fix.label }}</button>
			</CommitteeTable>
			<template v-if="!serviceIncident">
				<AttendeesTable :attendees="data.attendees || []" secondary :note="opening.closed ? '' : 'Saying who you represent does not show that a bid was submitted.'" />
				<div v-if="!opening.closed" class="kt-region is-secondary"><h2>Bids</h2>
					<div class="kt-group"><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty">Bids stay sealed until the committee opens them together. Nobody can see how many bids were received before then.</p></div>
				</div>
				<div v-if="primary === 'start'" class="kt-decision">
					<p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">Starting opens the bids one at a time, in front of the committee and attendees. Every member must stay present until the opening ends.</p>
					<div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bop-start" @click="run('begin_opening')">Start opening</button></div>
				</div>
				<div v-if="primary === 'join'" class="kt-decision">
					<p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">Joining tells the committee you are present. Stay on this page until the opening ends; if you leave, the opening pauses until you return.</p>
					<div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bop-join" @click="run('join_opening')">Join opening</button></div>
				</div>
				<History title="History" :summary="historySummary" />
			</template>
		</template>

		<!-- in session: c4–c9, c13, c13b, c7, c8, c8b, z1 -->
		<template v-else-if="mode === 'session'">
			<!-- z1 -->
			<template v-if="primary === 'end_no_bids'">
				<div class="kt-region"><h2>Bids</h2>
					<div class="kt-empty"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 8v13H3V8"></path><path d="M1 3h22v5H1z"></path><path d="M10 12h4"></path></svg><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty">There are no bids to open. The register will be empty.</p></div>
				</div>
				<div class="kt-decision">
					<p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">Ending records that there were no bids and closes the session. The committee still signs the opening record. Nothing is passed to Evaluation.</p>
					<div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bop-end-no-bids" @click="run('end_opening_with_no_bids')">End opening with no bids</button></div>
				</div>
				<CommitteeTable :members="members" secondary />
			</template>

			<!-- c7: a request made during the opening -->
			<template v-else-if="form === 'request'">
				<div class="kt-region" data-testid="bop-request-form"><h2>Request during opening</h2>
					<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px 24px;max-width:1000px">
						<div class="kt-field"><label for="bop-request-by">Asked by</label><input id="bop-request-by" v-model="draft.speaker" class="kt-input" data-testid="bop-request-by"></div>
						<div class="kt-field"><label for="bop-request-bid">Bid</label><select id="bop-request-bid" v-model="draft.entry" class="kt-input"><option v-for="e in readOut" :key="e.entry" :value="e.entry">{{ e.number }} · {{ e.tenderer }}</option></select></div>
						<div class="kt-field"><label for="bop-request-at">Asked at</label><input id="bop-request-at" v-model="draft.at" class="kt-input" placeholder="hh:mm:ss" data-testid="bop-request-at"></div>
						<div class="kt-field" style="grid-column:1 / -1"><label for="bop-request-what">What was asked</label><input id="bop-request-what" v-model="draft.what" class="kt-input" data-testid="bop-request-what"></div>
						<div class="kt-field" style="grid-column:1 / -1"><label for="bop-request-response">How it was answered</label><textarea id="bop-request-response" v-model="draft.response" class="kt-input" rows="3" data-testid="bop-request-response"></textarea></div>
					</div>
					<p v-if="error" class="bop-field-error" role="alert">{{ error }}</p>
					<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending || !draft.what.trim() || !draft.speaker.trim()" data-testid="bop-request-record" @click="recordRequest">Record as answered during opening</button><button type="button" class="kt-btn kt-btn-secondary" @click="closeForm">Cancel</button></div>
				</div>
				<RegisterTable :rows="register" secondary note="The request does not change the bid." />
				<History title="Evidence details" :summary="evidenceSummary" :rows="evidenceRows" />
			</template>

			<!-- c13: a comment for Evaluation -->
			<template v-else-if="form === 'comment'">
				<div class="kt-region" data-testid="bop-comment-form"><h2>Comment for Evaluation</h2>
					<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px 24px;max-width:1000px">
						<div class="kt-field"><label for="bop-comment-by">Made by</label><select id="bop-comment-by" v-model="draft.speaker" class="kt-input" data-testid="bop-comment-by"><option v-for="p in speakers" :key="p" :value="p">{{ p }}</option></select></div>
						<div class="kt-field"><label for="bop-comment-bid">Bid</label><select id="bop-comment-bid" v-model="draft.entry" class="kt-input"><option v-for="e in readOut" :key="e.entry" :value="e.entry">{{ e.number }} · {{ e.tenderer }}</option></select></div>
						<div class="kt-field"><label for="bop-comment-at">Time made (as you heard it)</label><input id="bop-comment-at" v-model="draft.at" class="kt-input" placeholder="hh:mm:ss"></div>
						<div class="kt-field" style="grid-column:1 / -1"><label for="bop-comment-text">Comment</label><textarea id="bop-comment-text" v-model="draft.what" class="kt-input" rows="2" data-testid="bop-comment-text"></textarea></div>
						<div class="kt-field" style="grid-column:1 / -1"><label for="bop-comment-response">Response</label><textarea id="bop-comment-response" v-model="draft.response" class="kt-input" rows="2" data-testid="bop-comment-response"></textarea></div>
					</div>
					<p style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">The comment is linked to the bid's receipt and to what was read aloud. The bid and the register do not change. Use this only for a factual comment. A bid that cannot be opened or matched is a problem for Opening access support, not a comment.</p>
					<p v-if="error" class="bop-field-error" role="alert">{{ error }}</p>
				</div>
				<div class="kt-decision"><p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">The Evaluation Committee receives this comment with the opened bid. It makes no decision at opening.</p><div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="kt-btn kt-btn-secondary" @click="closeForm">Cancel</button><button type="button" class="kt-btn kt-btn-primary" :disabled="pending || !draft.what.trim() || !draft.speaker" data-testid="bop-comment-record" @click="recordComment">Record comment for Evaluation</button></div></div>
				<History title="Evidence details" :summary="evidenceSummary" :rows="evidenceRows" />
			</template>

			<!-- c8: a member records their own differing account -->
			<template v-else-if="form === 'account'">
				<div class="kt-region" data-testid="bop-account-form"><h2>Record my differing account</h2>
					<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px 24px;max-width:1000px">
						<div class="kt-field"><label for="bop-account-bid">Bid</label><select id="bop-account-bid" v-model="draft.entry" class="kt-input"><option value="">No particular bid</option><option v-for="e in opened" :key="e.entry" :value="e.entry">{{ e.number }} · {{ e.tenderer }}</option></select></div>
						<div class="kt-field"><label for="bop-account-under">Recorded under</label><input id="bop-account-under" class="kt-input" :value="myRecordedUnder" readonly></div>
						<div class="kt-field" style="grid-column:1 / -1"><label for="bop-account-text">Your account, in your words</label><textarea id="bop-account-text" v-model="draft.what" class="kt-input" rows="3" data-testid="bop-account-text"></textarea></div>
					</div>
					<p style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">Your account is kept under your name. Only you can submit or change it. It does not change the bid or what was recorded as read aloud.</p>
					<p v-if="error" class="bop-field-error" role="alert">{{ error }}</p>
					<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending || !draft.what.trim()" data-testid="bop-account-record" @click="recordAccount">Record my differing account</button><button type="button" class="kt-btn kt-btn-secondary" @click="closeForm">Cancel</button></div>
				</div>
				<SessionTable :rows="chronology" />
				<History title="Evidence details" :summary="evidenceSummary" :rows="evidenceRows" />
			</template>

			<!-- c8b: the recorder responds to a member's account -->
			<template v-else-if="primary === 'respond_account' && account">
				<div class="kt-region" data-testid="bop-respond-form"><h2>Response to a member’s account</h2>
					<div class="kt-group" style="margin-bottom:16px"><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty"><strong>{{ account.member }}, {{ account.time_label }}:</strong> {{ account.account }}</p></div>
					<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px 24px;max-width:1000px">
						<div class="kt-field"><label for="bop-respond-by">Repeated by</label><select id="bop-respond-by" v-model="draft.speaker" class="kt-input" data-testid="bop-respond-by"><option v-for="m in members" :key="m.member_user" :value="m.full_name">{{ m.full_name }}</option></select></div>
						<div class="kt-field"><label for="bop-respond-at">Time repeated (as you heard it)</label><input id="bop-respond-at" v-model="draft.at" class="kt-input" placeholder="hh:mm:ss"></div>
						<div class="kt-field" style="grid-column:1 / -1"><label for="bop-respond-text">Response</label><textarea id="bop-respond-text" v-model="draft.response" class="kt-input" rows="2" data-testid="bop-respond-text"></textarea></div>
					</div>
					<p style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">Your response is linked to {{ account.member }}’s account. Their words stay as they recorded them.</p>
					<p v-if="error" class="bop-field-error" role="alert">{{ error }}</p>
					<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending || !draft.response.trim() || !draft.speaker" data-testid="bop-respond-record" @click="recordResponse">Record response</button></div>
				</div>
				<SessionTable :rows="chronology" />
				<History title="Evidence details" :summary="evidenceSummary" :rows="evidenceRows" />
			</template>

			<!-- c4: open the next bid -->
			<template v-else-if="primary === 'open_next'">
				<AttendeesTable :attendees="data.attendees || []" in-session :can-correct="viewer.is_recorder" note="People who joined before the start are carried into the session automatically. Departures are recorded when they happen." @correct="startAttendance" />
				<div class="kt-decision">
					<p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">Opening a bid shows it to the committee. Bids are opened one at a time.</p>
					<div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bop-open-next" @click="run('open_next_bid')">Open next bid</button></div>
				</div>
				<CommitteeTable :members="members" secondary />
				<History title="Evidence details" :summary="evidenceSummary" :rows="evidenceRows" />
			</template>

			<!-- c6: the recorder records what was read aloud -->
			<template v-else-if="primary === 'record_readout' && awaiting">
				<div class="kt-region" data-testid="bop-readout-form"><h2>What was read aloud</h2>
					<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px 24px;max-width:1000px">
						<div class="kt-field"><label for="bop-readout-by">Read aloud by</label><select id="bop-readout-by" v-model="draft.speaker" class="kt-input" data-testid="bop-readout-by"><option v-for="m in members" :key="m.member_user" :value="m.member_user">{{ m.full_name }}</option></select></div>
						<div class="kt-field"><label for="bop-readout-bid">Bid</label><input id="bop-readout-bid" class="kt-input" :value="`${awaiting.number} · ${awaiting.tenderer}`" readonly></div>
						<div class="kt-field"><label for="bop-readout-at">Time read aloud (as you heard it)</label><input id="bop-readout-at" v-model="draft.at" class="kt-input" placeholder="hh:mm:ss" data-testid="bop-readout-at"></div>
						<div class="kt-field"><label for="bop-readout-page">Page the committee will sign</label><select id="bop-readout-page" v-model.number="draft.page" class="kt-input" data-testid="bop-readout-page"><option v-for="n in awaiting.page_count" :key="n" :value="n">Page {{ n }}{{ n === 1 ? " (proposed, change if the committee chose another)" : "" }}</option></select></div>
						<div class="kt-field"><label for="bop-readout-price">Price page</label><input id="bop-readout-price" class="kt-input" :value="awaiting.price_page ? `Page ${awaiting.price_page} (found in the bid)` : 'Not found in the bid'" readonly></div>
					</div>
					<div style="margin-top:16px"><BidFacts :bid="awaiting" /></div>
					<p style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">These facts come from the opened bid and cannot be edited. The system records the time you confirm.</p>
					<p v-if="error" class="bop-field-error" role="alert" data-testid="bop-readout-error">{{ error }}</p>
				</div>
				<div class="kt-decision">
					<p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">Recording adds bid {{ awaiting.number }} to the opening register exactly as shown, records the pages each member will sign, and shows the bid on the public Tender page.</p>
					<div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending || !draft.speaker" data-testid="bop-record-readout" @click="recordReadout">Record what was read aloud</button></div>
				</div>
				<RegisterTable :rows="register" secondary />
				<History title="Evidence details" :summary="evidenceSummary" :rows="evidenceRows" />
			</template>

			<!-- c5: the member reads the bid aloud -->
			<template v-else-if="primary === 'read_aloud' && awaiting">
				<div class="kt-region" data-testid="bop-read-aloud"><h2>Bid {{ awaiting.number }}</h2>
					<BidFacts :bid="awaiting" />
					<div style="margin-top:20px;padding:16px 20px;border-left:3px solid var(--color-neutral-400)"><div class="kt-label" style="margin-bottom:6px">Read aloud</div><p style="margin:0;font-size:20px;line-height:1.45" data-testid="bop-read-aloud-text">{{ awaiting.read_aloud }}</p></div>
					<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><a class="kt-btn kt-btn-secondary" :href="bidPagesUrl(awaiting)" target="_blank" rel="noopener" data-testid="bop-view-bid-pages">View bid pages</a></div>
				</div>
				<CommitteeTable :members="members" secondary />
				<History title="Evidence details" :summary="evidenceSummary" :rows="evidenceRows" />
			</template>

			<!-- c9 / c13b: every bid read out; end the opening -->
			<template v-else-if="primary === 'end'">
				<template v-if="justCommented">
					<RequestsTable :rows="requests" with-response :note="commentNote" />
					<RegisterTable :rows="register" secondary />
					<div class="kt-decision"><div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bop-end" @click="run('end_opening')">End opening</button></div></div>
				</template>
				<template v-else>
					<RegisterTable :rows="register" :note="signingNote" />
					<RequestsTable :rows="requests" secondary note="Use Record comment for Evaluation only for a factual comment that was not resolved during the opening. It does not score or reject the bid.">
						<button type="button" class="kt-btn kt-btn-secondary" data-testid="bop-open-comment" @click="openForm('comment')">Record comment for Evaluation</button>
						<button type="button" class="kt-btn kt-btn-secondary" data-testid="bop-open-request" @click="openForm('request')">Record a request</button>
					</RequestsTable>
					<div class="kt-decision">
						<p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">Ending closes the session and fixes the register. You then prepare the opening record for the committee to sign.</p>
						<div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bop-end" @click="run('end_opening')">End opening</button></div>
					</div>
					<History title="Evidence details" :summary="evidenceSummary" :rows="evidenceRows" />
				</template>
			</template>

			<!-- waiting: a member while the chair continues, or the chair while the recorder records -->
			<template v-else>
				<div v-if="awaiting" class="kt-region" data-testid="bop-bid-opened"><h2>Bid {{ awaiting.number }}</h2><BidFacts :bid="awaiting" /></div>
				<SessionTable :rows="chronology" :secondary="!!awaiting" />
				<RegisterTable v-if="register.length" :rows="register" secondary />
				<div v-if="viewer.is_member && !viewer.is_recorder" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="kt-btn kt-btn-secondary" data-testid="bop-open-account" @click="openForm('account')">Record my differing account</button></div>
				<CommitteeTable :members="members" secondary />
				<History title="Evidence details" :summary="evidenceSummary" :rows="evidenceRows" />
			</template>
		</template>

		<!-- paused: c10 (member absent), c11–c11d (a bid problem), c11e (Accounting Officer) -->
		<template v-else-if="mode === 'paused-member'">
			<CommitteeTable :members="members">
				<button v-for="m in absentMembers" v-show="viewer.is_chair" :key="m.member_user" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" :data-testid="`bop-notify-${m.member_user}`" @click="run('notify_member', { member: m.member_user })">Notify {{ m.full_name }}</button>
			</CommitteeTable>
			<div v-if="primary === 'join'" class="kt-decision">
				<p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">The opening is paused until you rejoin. It continues from the last recorded step.</p>
				<div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bop-join" @click="run('join_opening')">Rejoin opening</button></div>
			</div>
			<ReplacementForm v-if="primary === 'appoint_replacement'" :members="members" :candidates="data.candidates || []" :pending="pending" :error="error" @appoint="appointReplacement" />
			<div class="kt-region is-secondary"><h2>Where the opening stopped</h2>
				<div class="kt-group"><div class="kt-meta-row"><div><span class="kt-label">Last recorded step</span><span class="kt-meta-value">{{ lastStep }}</span></div></div><p style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">Nothing else is recorded, opened or ended until every member is present. When they rejoin, you continue from here.</p></div>
			</div>
			<History title="Evidence details" :summary="evidenceSummary" :rows="evidenceRows" />
		</template>

		<template v-else-if="mode === 'ao-decision'">
			<div class="kt-region" data-testid="bop-why-paused"><h2>Why the opening is paused</h2>
				<div class="kt-meta-row"><div><span class="kt-label">Bid</span><span class="kt-meta-value">Receipt {{ pause.receipt }}</span></div><div><span class="kt-label">Problem</span><span class="kt-meta-value">{{ problemText }}</span></div><div><span class="kt-label">Handled by</span><span class="kt-meta-value">Opening access support</span></div><div><span class="kt-label">Last recorded step</span><span class="kt-meta-value">{{ lastStep }}</span></div></div>
				<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="kt-btn kt-btn-secondary" @click="showProblem = !showProblem">View problem details</button></div>
				<p style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">If support fixes the problem, the chair can resume the opening once every member has rejoined. Nothing from the bid has been read aloud or shown.</p>
			</div>
			<div class="kt-region" data-testid="bop-tender-decision"><h2>Tender decision</h2>
				<div class="kt-group"><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty">{{ data.decision.unavailable_text }}</p></div>
			</div>
		</template>

		<template v-else-if="mode === 'paused-bid'">
			<div class="kt-region" data-testid="bop-bid-problem"><h2>{{ isMismatch ? "Bid being checked" : "Bid that could not be opened" }}</h2>
				<div v-if="isMismatch" class="kt-meta-row"><div><span class="kt-label">Receipt</span><span class="kt-meta-value">{{ pause.receipt }}</span></div><div><span class="kt-label">Found at</span><span class="kt-meta-value">{{ pause.since_label }}</span></div><div><span class="kt-label">Being checked by</span><span class="kt-meta-value">Opening access support</span></div></div>
				<div v-else class="kt-meta-row"><div><span class="kt-label">Receipt</span><span class="kt-meta-value">{{ pause.receipt }}</span></div><div><span class="kt-label">Tried to open</span><span class="kt-meta-value">{{ pause.since_label }}</span></div><div><span class="kt-label">Being checked by</span><span class="kt-meta-value">Opening access support</span></div><div><span class="kt-label">Status</span><span class="kt-meta-value" data-testid="bop-problem-status"><span v-if="incidentStatus === 'Resolved'" class="kt-status is-live">Resolved {{ incidentResolved }}</span><span v-else-if="incidentStatus === 'Unresolved'" class="kt-status is-critical">Not resolved</span><template v-else>Being checked</template></span></div></div>
				<p style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">{{ isMismatch ? "The bid cannot be replaced or left out. The opening cannot finish until there is a documented outcome." : "The bid is not skipped or rejected. Nothing from it has been read aloud or shown." }}</p>
				<div v-if="!isMismatch && viewer.is_chair" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px">
					<template v-if="primary === 'retry'"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bop-retry" @click="run('retry_opening')">Retry opening</button><button type="button" class="kt-btn kt-btn-secondary" @click="showProblem = !showProblem">View problem details</button></template>
					<template v-else-if="incidentStatus === 'Unresolved'"><button type="button" class="kt-btn kt-btn-secondary" @click="showProblem = !showProblem">View problem details</button></template>
					<template v-else><button type="button" class="kt-btn kt-btn-secondary" disabled data-testid="bop-retry">Retry opening</button><span style="font-size:13px;color:var(--color-neutral-800)">Available when support marks the problem resolved</span></template>
				</div>
			</div>
			<CommitteeTable :members="members" secondary />
			<History title="Problem details" :summary="`Reference ${pause.incident ? pause.incident.incident_id : ''}`" :rows="problemRows" />
		</template>

		<!-- c12: ended by Tender cancellation -->
		<template v-else-if="mode === 'cancelled'">
			<div class="kt-region" data-testid="bop-cancelled"><h2>{{ data.cancellation.message }}</h2>
				<div class="kt-meta-row"><div><span class="kt-label">Opening started</span><span class="kt-meta-value">{{ startedAt }}</span></div><div><span class="kt-label">Last recorded step</span><span class="kt-meta-value">{{ lastChronology }}</span></div></div>
				<p style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">{{ data.cancellation.note }} Cancellation notices are handled with the Tender.</p>
			</div>
			<SessionTable :rows="chronology" title="Session up to cancellation" />
			<History title="Evidence details" :summary="evidenceSummary" :rows="evidenceRows" />
		</template>

		<!-- n1: the opening has not started; the Accounting Officer records what happened -->
		<template v-else-if="mode === 'not-held-due'">
			<div class="kt-region" data-testid="bop-not-held-form"><h2>Record what happened</h2>
				<div class="kt-meta-row"><div><span class="kt-label">Scheduled</span><span class="kt-meta-value">{{ opening.deadline_label }}</span></div><div v-if="firstIncident"><span class="kt-label">Problem</span><span class="kt-meta-value">{{ firstIncident.type }}, recorded by Opening access support<template v-if="firstIncident.notified_label"> at {{ firstIncident.notified_label }}</template></span></div><div><span class="kt-label">Bids</span><span class="kt-meta-value">Still sealed</span></div></div>
				<div style="margin-top:16px"><div style="display:grid;grid-template-columns:repeat(1,minmax(0,1fr));gap:16px 24px;max-width:1000px"><div class="kt-field"><label for="bop-not-held-reason">Reason</label><input id="bop-not-held-reason" v-model="draft.what" class="kt-input" data-testid="bop-not-held-reason"></div></div></div>
				<p v-if="error" class="bop-field-error" role="alert">{{ error }}</p>
			</div>
			<div class="kt-decision">
				<p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">This is final for this opening: it cannot be started later on this record. The bids stay sealed and you then decide what happens next for the Tender.</p>
				<div style="display:flex;justify-content:flex-end;gap:12px"><button type="button" class="kt-btn kt-btn-primary" :disabled="pending || !draft.what.trim()" data-testid="bop-record-not-held" @click="run('record_not_held', { reason: draft.what.trim() })">Record that opening did not take place</button></div>
			</div>
		</template>

		<!-- n2: it did not take place -->
		<template v-else-if="mode === 'not-held'">
			<div class="kt-region" data-testid="bop-not-held"><h2>The opening did not take place</h2>
				<div class="kt-meta-row"><div v-if="data.decision"><span class="kt-label">Recorded</span><span class="kt-meta-value">{{ data.decision.recorded_label }} by {{ data.decision.holder }}</span></div><div v-if="data.decision"><span class="kt-label">Reason</span><span class="kt-meta-value">{{ data.decision.reason }}</span></div><div><span class="kt-label">Bids</span><span class="kt-meta-value">Still sealed</span></div></div>
				<div v-if="firstIncident" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px"><button type="button" class="kt-btn kt-btn-secondary" @click="showProblem = !showProblem">View problem details</button></div>
			</div>
			<div v-if="data.decision" class="kt-region"><h2>Tender decision</h2>
				<div class="kt-group"><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty">{{ data.decision.unavailable_text }}</p></div>
			</div>
			<div class="kt-region is-secondary"><h2>What this means</h2>
				<div class="kt-group"><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty">No bids were opened and there is no opening record. The Tender is not cancelled or rescheduled by this record.</p></div>
			</div>
		</template>

		<div v-if="showProblem && (data.incidents || []).length" class="bop-problem-details" data-testid="bop-problem-details" role="region" aria-label="Problem details">
			<table class="kt-table"><thead><tr><th>Reference</th><th>Problem</th><th>Handled by</th><th>Notice</th></tr></thead><tbody>
				<tr v-for="i in data.incidents" :key="i.incident_id"><td>{{ i.incident_id }}</td><td>{{ i.type }}</td><td>{{ i.holder }}</td><td>{{ i.notification_state }}<template v-if="i.notified_label"> {{ i.notified_label }}</template></td></tr>
			</tbody></table>
		</div>

		<AttendanceDialog v-if="attendanceFor" :attendee="attendanceFor" :pending="pending" @confirm="recordAttendance" @cancel="attendanceFor = null" />
	</div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import AttendanceDialog from "../components/AttendanceDialog.vue";
import AttendeesTable from "../components/AttendeesTable.vue";
import BidFacts from "../components/BidFacts.vue";
import CommitteeTable from "../components/CommitteeTable.vue";
import Guidance from "../components/Guidance.vue";
import History from "../components/History.vue";
import PageHead from "../components/PageHead.vue";
import RegisterTable from "../components/RegisterTable.vue";
import ReplacementForm from "../components/ReplacementForm.vue";
import RequestsTable from "../components/RequestsTable.vue";
import SessionTable from "../components/SessionTable.vue";
import { pagesUrl } from "../data/api.js";

const props = defineProps({ data: { type: Object, required: true }, pending: Boolean, error: { type: String, default: "" }, refusal: { type: Object, default: null } });
const emit = defineEmits(["command"]);

const opening = computed(() => props.data.opening);
const viewer = computed(() => props.data.viewer || {});
const members = computed(() => props.data.committee.members || []);
const ceremony = computed(() => props.data.ceremony || {});
const register = computed(() => ceremony.value.register || []);
const opened = computed(() => ceremony.value.opened || []);
const readOut = computed(() => opened.value.filter((e) => e.status === "Read out"));
const awaiting = computed(() => ceremony.value.awaiting_readout || null);
const requests = computed(() => ceremony.value.requests || []);
const chronology = computed(() => ceremony.value.chronology || []);
const pause = computed(() => ceremony.value.pause || {});
const account = computed(() => (ceremony.value.accounts || []).find((a) => !a.responded) || null);
const primary = computed(() => (props.data.next_step && props.data.next_step.primary_action) || "");
const state = computed(() => opening.value.state);

const mode = computed(() => {
	if (state.value === "Not held") return "not-held";
	if (state.value === "Cancelled after start") return "cancelled";
	if (primary.value === "record_not_held") return "not-held-due";
	if (state.value === "Interrupted") {
		if (pause.value.class === "Member absent") return "paused-member";
		if (props.data.decision && viewer.value.is_accounting_officer && !viewer.value.is_member) return "ao-decision";
		return "paused-bid";
	}
	if (state.value === "Opening") return "session";
	return "pre";
});

// local forms (c7, c8, c13) and the confirmation just after a comment (c13b)
const form = ref("");
// Board c13b: right after a comment for Evaluation (the last thing recorded).
const justCommented = computed(() => {
	const last = requests.value[requests.value.length - 1];
	const event = chronology.value[chronology.value.length - 1];
	return !!last && last.exception_class === "Comment for Evaluation" && !!event && event.what === `${last.speaker_name}: ${last.observed_fact}`;
});
const showProblem = ref(false);
const attendanceFor = ref(null);
const draft = reactive({ speaker: "", entry: "", at: "", what: "", response: "", page: 1 });
function resetDraft() {
	Object.assign(draft, { speaker: "", entry: (readOut.value[0] || opened.value[0] || {}).entry || "", at: "", what: "", response: "", page: 1 });
}
function openForm(kind) {
	resetDraft();
	if (kind === "comment") {
		draft.speaker = speakers.value[0] || "";
		draft.response = "The observation is recorded for the Evaluation Committee to check. No decision is made at opening.";
	}
	form.value = kind;
}
function closeForm() {
	form.value = "";
}
watch(() => [awaiting.value && awaiting.value.entry, primary.value], () => {
	resetDraft();
	if (primary.value === "record_readout" && awaiting.value) {
		const reader = members.value.find((m) => !m.is_chair && !m.is_recorder) || members.value[0];
		draft.speaker = reader ? reader.member_user : "";
	}
	if (primary.value === "respond_account") draft.speaker = (members.value.find((m) => !m.is_chair && !m.is_recorder) || members.value[0] || {}).full_name || "";
}, { immediate: true });

const answer = computed(() => {
	if (form.value === "account") return null; // board c8: the member's own form carries no next step
	if (form.value === "request") return { kind: "your_turn", label: "Your turn", headline: "Record a request made during the opening", sentence: "", fixes: [], blockers: [] };
	if (form.value === "comment") return { kind: "your_turn", label: "Your turn", headline: "Record comment for Evaluation", sentence: "", fixes: [], blockers: [] };
	return props.data.next_step;
});

// before Start
const fixes = computed(() => ((props.data.next_step && props.data.next_step.blockers) || []).flatMap((b) => b.fixes || []));
const notifyFixes = computed(() => (viewer.value.is_chair ? fixes.value.filter((f) => f.fix_id === "notify_member") : []));
const serviceIncident = computed(() => (props.data.incidents || []).find((i) => i.type === "Opening profile unavailable") || null);
const problemRow = computed(() => !serviceIncident.value && (props.data.next_step || {}).kind === "waiting" && fixes.value.some((f) => f.fix_id === "view_problem_details"));
const historySummary = computed(() => {
	const c = props.data.committee || {};
	const a = props.data.arrangements || {};
	return [c.appointed_label && `Committee appointed ${c.appointed_label}`, a.published && `attendance published ${a.published_label}`].filter(Boolean).join(" · ");
});

// in session and paused
const evidenceSummary = computed(() => {
	const receipt = (awaiting.value || register.value[0] || opened.value[0] || {}).receipt;
	return receipt ? `Receipt ${receipt} · event history` : "Event history";
});
const evidenceRows = computed(() => chronology.value.map((r) => [r.time, r.who, r.what]));
const signingNote = computed(() => {
	const r = register.value[0];
	return r ? `Pages for signing: bid page ${r.pages || 1}${r.price_page ? `, price page ${r.price_page}` : ""}.` : "";
});
const commentNote = computed(() => {
	const c = [...requests.value].reverse().find((r) => r.exception_class === "Comment for Evaluation");
	const bid = c && (opened.value.find((e) => e.entry === c.entry) || {}).number;
	return c ? `Recorded by ${c.recorded_by} at ${c.recorded_label}${bid ? `, linked to bid ${bid}` : ""}.` : "";
});
const speakers = computed(() => [...members.value.map((m) => `${m.full_name} · ${m.committee_role}`), ...(props.data.attendees || []).map((a) => a.person_name)]);
const myRecordedUnder = computed(() => {
	const me = members.value.find((m) => m.member_user === frappe.session.user);
	return me ? `${me.full_name} · ${me.committee_role}` : "";
});
const absentMembers = computed(() => members.value.filter((m) => !m.present));
const lastStep = computed(() => {
	const last = pause.value.last_step || {};
	return last.what ? `${last.what}${last.at_label ? `, ${last.at_label}` : ""}` : "Nothing recorded yet";
});
const isMismatch = computed(() => pause.value.class === "Package mismatch");
const incidentStatus = computed(() => (pause.value.incident || {}).status || "");
const incidentResolved = computed(() => {
	const at = (pause.value.incident || {}).resolved_at;
	return at ? String(at).slice(11, 16) : "";
});
const problemText = computed(() => (isMismatch.value ? "The bid did not match the submissions received at the deadline" : "The bid could not be opened"));
const problemRows = computed(() => (props.data.incidents || []).map((i) => [i.incident_id, i.type, i.holder, i.notification_state]));
const startedAt = computed(() => (chronology.value[0] || {}).time || "");
const lastChronology = computed(() => {
	const last = chronology.value[chronology.value.length - 1];
	return last ? `${last.what}, ${last.time}` : "";
});
const firstIncident = computed(() => (props.data.incidents || [])[0] || null);

function bidPagesUrl(bid) {
	return pagesUrl(opening.value.tender_reference, "bid", bid.entry);
}
function reportedAt(value) {
	// "hh:mm[:ss]" as heard, on the opening's own day; empty means "now".
	const text = String(value || "").trim();
	if (!text) return "";
	const day = String(opening.value.deadline || "").slice(0, 10);
	return /^\d{1,2}:\d{2}(:\d{2})?$/.test(text) ? `${day} ${text.length === 5 ? `${text}:00` : text}` : text;
}
function run(method, args = {}) {
	emit("command", { method, args });
}
function onFix(fix) {
	if (fix.fix_id === "notify_member") run("notify_member", { member: fix.target });
	else if (fix.fix_id === "notify_support") run("notify_support", { incident: fix.target || (serviceIncident.value || {}).incident_id });
	else if (fix.fix_id === "view_problem_details") showProblem.value = !showProblem.value;
}
function recordReadout() {
	run("record_readout", { entry: awaiting.value.entry, speaker: draft.speaker, designated_pages: JSON.stringify([draft.page]), reported_speech_at: reportedAt(draft.at) });
}
function recordRequest() {
	run("record_intervention", { exception_class: "Repeat request", speaker_name: draft.speaker.trim(), what: draft.what.trim(), response: draft.response.trim(), entry: draft.entry, reported_at: reportedAt(draft.at) });
	form.value = "";
}
function recordComment() {
	run("record_comment_for_evaluation", { entry: draft.entry, made_by: draft.speaker.split(" · ")[0], comment: draft.what.trim(), response: draft.response.trim(), reported_at: reportedAt(draft.at) });
	form.value = "";
}
function recordAccount() {
	run("record_member_account", { account: draft.what.trim(), entry: draft.entry });
	form.value = "";
}
function recordResponse() {
	run("record_intervention", { exception_class: "Procedural comment", speaker_name: draft.speaker, what: `Response to ${account.value.member}’s account`, response: draft.response.trim(), linked_account: account.value.event_id, reported_at: reportedAt(draft.at) });
}
function startAttendance(attendee) {
	attendanceFor.value = attendee;
}
function recordAttendance(values) {
	run("record_attendance", { ...values, reported_at: reportedAt(values.reported_at) });
	attendanceFor.value = null;
}
function appointReplacement(values) {
	run("appoint_committee", values);
}
</script>
