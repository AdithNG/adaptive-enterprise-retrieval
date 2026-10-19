import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';

const root = process.cwd();
const runtime = process.env.RUNTIME_NODE_MODULES;
const skill = process.env.PRESENTATIONS_SKILL_DIR;
if (!runtime || !skill) throw new Error('Set RUNTIME_NODE_MODULES and PRESENTATIONS_SKILL_DIR to the bundled runtime and skill.');
const require = createRequire(path.join(runtime, 'package.json'));
const {Presentation, PresentationFile} = await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const {finalizePresentation} = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href);
const build = path.join(root, '.tmp/midterm-slides');
const out = path.join(root, 'docs/presentation');
await fs.mkdir(build, {recursive:true});
await fs.mkdir(out, {recursive:true});
const deck = Presentation.create({slideSize:{width:1280,height:720}});
const ink = '#14283F', teal = '#087E8B', gray = '#526171';
function text(slide, copy, x,y,w,h,size=26,color=ink,bold=false) {
  const box=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  box.text=copy;
  box.text.style={typeface:'Arial',fontSize:size,color,bold};
  return box;
}
const s1=deck.slides.add();
s1.background.fill='#FFFFFF';
text(s1,'TEAM 13   /   CSCI 544 MIDTERM',64,30,1120,30,18,teal,true);
text(s1,'Cost-aware adaptive retrieval\nfor enterprise support',64,76,1140,112,46,ink,true);
text(s1,'Goal: reduce response time and cost while preserving answer quality',64,194,1140,42,26,gray);
text(s1,'THE TASK',64,267,500,30,20,teal,true);
text(s1,'Input: a support question and\ncompany documents\n\nTarget output: a cited answer,\nor refusal when evidence is weak',64,309,525,190,27);
text(s1,'PROPOSED METHOD',665,267,550,30,20,teal,true);
text(s1,'1   Reuse a verified cached answer\n2   Otherwise retrieve and rerank\n3   If evidence is weak, search once more\n4   Answer with citations or refuse',665,310,555,170,25);
text(s1,'Today: MiniLM retrieval baseline implemented',665,487,550,36,22,teal,true);
text(s1,'PRIOR WORK AND OUR FOCUS',64,548,1130,28,20,teal,true);
text(s1,'Adaptive-RAG (Jeong et al., 2024): routes by question complexity\nSelf-RAG (Asai et al., 2024): retrieves and critiques with self-reflection',64,585,1140,58,22);
text(s1,'Our planned contribution: evaluate cache reuse and bounded retries on enterprise data, measuring quality against latency and cost.',64,655,1140,48,21,gray);
s1.speakerNotes.text=`Speaking target: 55 seconds.
We are building a support assistant that takes a question and company documents and aims to return a cited answer, or refuse when the evidence is insufficient. Our research question is whether adapting retrieval effort can reduce latency and cost while preserving quality. The planned pipeline first checks a verified cache. For novel questions it retrieves and reranks evidence, permits one additional search when needed, and then answers or refuses. Today we have implemented the retrieval baseline. Adaptive-RAG routes according to question complexity, and Self-RAG learns retrieval and self-reflection. We build on those ideas with an application-focused evaluation of verified cache reuse and bounded retries on enterprise support data. Cost savings remain a hypothesis.

Sources:
Jeong et al., Adaptive-RAG, NAACL 2024: https://aclanthology.org/2024.naacl-long.389/
Asai et al., Self-RAG, ICLR 2024: https://arxiv.org/abs/2310.11511
Team proposal and implementation: https://github.com/AdithNG/adaptive-enterprise-retrieval/tree/midterm-presentation
Distinction: this is an applied evaluation contribution, not a claim that adaptive routing itself is new. No training or routing implementation is claimed complete.`;

const s2=deck.slides.add();
s2.background.fill='#FFFFFF';
text(s2,'TEAM 13   /   RESULTS AND NEXT STEPS',64,30,1120,30,18,teal,true);
text(s2,'Retrieval works, but semantic queries lag',64,83,1160,66,43,ink,true);
text(s2,'EnterpriseRAG-Bench subset: 100 questions, 290 documents, 3,358 indexed passages',64,158,1150,38,23,gray);
text(s2,'84.4%',64,223,360,83,68,teal,true);
text(s2,'Overall Hit@5\n76 of 90 answerable questions',64,315,360,63,23);
text(s2,'64.0%',478,223,360,83,68,teal,true);
text(s2,'Semantic Hit@5\n16 of 25 semantic questions',478,315,360,63,23);
text(s2,'0.670',892,223,310,83,68,teal,true);
text(s2,'Mean reciprocal rank\nAcross 90 answerable questions',892,315,320,63,23);
text(s2,'Completed: subset, chunking, MiniLM search, evaluation. Reproduced every gold rank.',64,405,1150,40,23,gray);
text(s2,'WHAT WE LEARNED',64,472,530,30,20,teal,true);
text(s2,'The correct document can rank first\nwhile its top passage omits the answer.\nWe still need to verify answer evidence.',64,514,530,117,25);
text(s2,'BEFORE THE FINAL REPORT',665,472,550,30,20,teal,true);
text(s2,'Grounded answers and refusal\nReranking, cache and one extra search\nCompare quality, latency and cost\nAdd questions spanning multiple documents',665,514,550,130,24);
text(s2,'Exploratory results pooled across splits. Ten unanswerable questions excluded. Answer quality and adaptive savings remain unmeasured.',64,665,1150,42,18,gray);
s2.speakerNotes.text=`Speaking target: 65 seconds, followed by about one minute for Q&A.
We now have a reproducible baseline using 100 questions and 290 documents. We chunked them into 3,358 model-safe passages and indexed them with MiniLM. On the 90 questions with gold documents, the correct document appears in the top five 84.4 percent of the time. Semantic questions are weaker, at 64 percent. MRR is 0.670. A local rerun reproduced all 100 gold-document ranks from the earlier run. Our main takeaway is that document retrieval is promising but does not guarantee usable answer evidence. In one example the correct document ranked first, but its best chunk omitted the five-business-day detail needed to answer. Next we need grounded generation and refusal, then reranking, verified cache and bounded requery. We will compare answer quality, latency and cost and expand to multi-document questions.

Results source: https://github.com/AdithNG/adaptive-enterprise-retrieval/blob/midterm-presentation/results/midterm/retrieval_eval_20261019-023503/summary.json
Manual examples: https://github.com/AdithNG/adaptive-enterprise-retrieval/blob/midterm-presentation/results/midterm/retrieval_eval_20261019-023503/REVIEW.md
Dataset: https://github.com/onyx-dot-app/EnterpriseRAG-Bench

Q&A:
What is Hit@5? The fraction of answerable questions with at least one gold document among the first five ranked documents.
What is MRR? Average reciprocal rank of the first gold document. It is not average rank.
Why 290 documents? A manageable corpus with 90 gold documents and 200 other referenced documents selected as hard negatives. We have not established full-corpus performance.
Have you reduced cost? Not yet. This run measures retrieval only. Adaptive comparisons are future work.
Does it evaluate refusal? No. Ten info-not-found questions are logged but excluded from retrieval scoring.
What about held-out performance? Test Hit@5 is 12/15, but this small split is descriptive: earlier pooled scores were already inspected. No tuning was performed for this reproduction.
Multi-document coverage? No current answerable question has multiple gold documents; adding that coverage is planned.
Failure example: qst_0187 asks about harmful-output warnings across two evaluation windows. Gold document ranks sixth while general incident guidance ranks first.
Success limitation: qst_0046 has the correct document at rank one, but the top chunk starts after the five-day runbook detail. Full document retrieval success is not answer correctness.`;

for(let i=0;i<deck.slides.items.length;i++){
  const png=await deck.export({slide:deck.slides.items[i],format:'png',scale:1});
  await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));
}
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
const result=await finalizePresentation({
  workspaceDir:root,candidatePath:candidate,finalPath:path.join(out,'Team13-Midterm.pptx'),
  pythonExecutable:process.env.RUNTIME_PYTHON,
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
  explicitTotalSlideCount:2,fontPolicy:{basis:'design',families:['Arial']},
  verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json'),
});
console.log(JSON.stringify(result));
