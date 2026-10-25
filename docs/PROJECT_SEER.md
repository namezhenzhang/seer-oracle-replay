Project Seer: Predictive Runtime for Heterogeneous Agent Computing

# 1. Executive Summary

AI infrastructure today is largely optimized around independent model-inference requests. Long-running agents behave very differently: they plan, execute deterministic code, call browsers and tools, wait on networks and external services, suspend and resume, spawn sub-agents, share context, and later converge to synthesize results. The central thesis of Project Seer is that an agent program exposes information about its future execution that conventional infrastructure does not fully use.

If the runtime can predict what an agent will need next—CPU, GPU, memory, browser capacity, network, or model inference—it may be possible to schedule work before demand arrives. This could reduce idle resources, improve concurrency, lower cost per successful task, and potentially motivate new hardware/software co-design.

The immediate goal is not to form a company or build custom hardware. The first goal is a UCSB research project that measures the systems value of agent foreknowledge. If the effect is large enough to change infrastructure economics, the research could become the basis for a standalone agent-infrastructure startup.

# 2. The Problem: Agent Computing Is a Different Workload

Traditional LLM serving largely sees a stream of requests: prefill, decode, return tokens. Agent execution is a heterogeneous, long-lived workflow. A typical computer-use or research agent may alternate repeatedly among model inference, Python or code execution, browser interaction, DOM or screenshot processing, filesystem operations, networking, tool calls, waiting, and orchestration.

This suggests that the bottleneck for agents may not simply be GPU utilization. The more interesting hypothesis is that the host-side execution substrate becomes the limiting factor as agents scale. CPU compute, browser execution, serialization, state management, network waits, process scheduling, memory usage, and synchronization can all prevent expensive GPU resources from doing useful work.

The key systems question is therefore broader than “How do we make inference faster?” It is: “How do we maximize productive work across the entire heterogeneous machine while thousands of agents continuously block, wake, branch, migrate, and resume?”

# 3. Core Insight: Agent Foreknowledge

Unlike generic serving workloads, agents may expose partial information about their future. The runtime may know or predict that an agent will resume after a tool call, that multiple child agents share the same parent context, that a synthesis stage will begin when several branches converge, or that a deterministic code path is likely to call an LLM only when a particular exception occurs.

This information can potentially be transformed into predictions of future resource demand:

- When will an agent resume?
- Which context or state will be reused, and by which agents?
- Which branches will fan out, terminate, or converge?
- When will the workflow need CPU, browser, network, memory, or GPU inference?
- Which model is likely to be needed next, and how much generation is expected?
- Which state can be evicted, checkpointed, migrated, recomputed, or prefetched?

The distinctive thesis is not merely to cache better. It is to use execution semantics to act before the next request arrives.

# 4. Why Neuro-Symbolic and Reusable Code Plans Are Especially Interesting

Simular’s neuro-symbolic direction provides a strong motivating example. Reusable code plans reduce repeated LLM reasoning by converting successful workflows into deterministic or semi-deterministic programs. That has an additional systems benefit: it makes future execution structure more explicit.

A reusable plan can reveal known steps, expected tool calls, parallel sections, branch points, likely failure modes, and where LLM fallback may occur. This creates two complementary optimization layers:

- Semantic optimizer: What should the agent do?
- Systems optimizer: How should that agent program execute efficiently?

Project Seer focuses on the second layer. The research hypothesis is that structured agent programs are not only cheaper semantically; they may also be substantially easier to schedule and provision ahead of time.

# 5. Proposed System: Predictive Runtime for Heterogeneous Agent Computing

The proposed runtime should sit above existing inference engines rather than compete directly with them. SGLang, vLLM, or NVIDIA Dynamo can remain responsible for model serving, kernels, batching, and low-level inference execution. Project Seer would reason over the longer-lived agent program and its heterogeneous resource needs.

Conceptually, the stack is:

- Agent program / execution graph / reusable code plan
- Project Seer predictive runtime: future-use prediction, scheduling, resource placement, prefetch, checkpoint/resume, model routing
- Existing execution backends: browser/runtime, SGLang/vLLM/Dynamo, CPU workers, storage, networking
- Physical resources: CPU, GPU, DRAM/HBM, CXL, NVMe, network, and potentially specialized data-movement hardware

The runtime should optimize total cost per completed task rather than any single resource in isolation.

# 6. Candidate Mechanisms

- Blocked-agent scheduling: reclaim CPU, browser, memory, or GPU-associated resources while an agent is waiting on tools or external I/O.
- Predictive prefetch: restore agent state shortly before the runtime expects an agent to resume.
- Sibling-aware execution: colocate or coordinate sub-agents that share parent context or environment state.
- Convergence planning: prepare synthesis resources before parallel branches finish.
- Model routing: use the code plan and execution state to anticipate when a small model, large model, or no model will be needed.
- Checkpoint and migration: suspend long-running agents and move them across machines without expensive full reconstruction.
- CPU/browser-aware scheduling: jointly schedule browser processes, tool workers, CPU compute, and model inference rather than optimizing each independently.
- Eventually, predictive data movement: move state across HBM, DRAM/CXL, NVMe, or nodes before it is demanded.

# 7. Research Questions

- How much wall-clock time do real agents spend in GPU inference, CPU work, browser execution, orchestration, network wait, storage, and idle states?
- How do these fractions change from 1 agent to 10, 100, and 1,000 concurrent agents?
- How predictable are suspend/resume times, branch structure, model calls, and future resource requirements?
- How much agent state is duplicated across sibling agents or repeated executions?
- How much could an oracle scheduler that knows the future save relative to a reactive scheduler?
- How much of the oracle gain remains achievable with imperfect learned predictions?
- Which resource becomes the next bottleneck after predictive scheduling is introduced?

# 8. Experimental Plan

## Phase 1 — Workload Characterization

Instrument representative computer-use, coding, and research-agent workloads. Measure CPU core-seconds, RAM GB-seconds, browser CPU/RAM, tool latency, I/O wait, model inference time, GPU utilization, GPU idle time caused by host-side delays, context reuse, branch structure, suspend/resume behavior, and total cost per successful task.

## Phase 2 — Value-of-Information Simulator

Replay traces under several increasingly informed schedulers: reactive request-level scheduling, lifecycle-aware scheduling, execution-graph-aware scheduling, predicted future demand, and an oracle with the actual future trace. The oracle defines the upper bound of the opportunity before substantial systems engineering begins.

## Phase 3 — One Real Mechanism

Implement the mechanism with the highest simulated value on top of an existing inference/runtime stack. Examples include blocked-agent eviction plus predictive resume, sibling-context sharing, or cross-resource scheduling of browser/CPU/GPU stages.

## Phase 4 — Economic Benchmark

Evaluate cost per successful task, agents per machine or GPU, CPU and GPU utilization, peak and time-weighted memory usage, bandwidth, P50/P95 task latency, and task success rate.

# 9. Success Criteria

The project should have a strict go/no-go bar. A single-digit optimization is likely to become a feature in an existing runtime. The opportunity becomes strategically interesting only if agent foreknowledge produces a large systems advantage—for example, substantially higher concurrency or a material reduction in total infrastructure cost per successful task while preserving task quality.

The research should explicitly test three possibilities:

- CPU or host compute is genuinely saturated: pursue CPU/browser/runtime scheduling and possibly specialized acceleration.
- CPU utilization is modest but agents and GPUs are frequently waiting: the primary problem is orchestration, I/O, synchronization, and prediction rather than raw CPU capacity.
- CPU and GPU are both well utilized but economics remain poor: memory hierarchy, inference efficiency, or data movement may be the more valuable next target.

# 10. Competitive Boundary

The project should avoid becoming another generic GPU optimization, KV-cache, or memory-tiering effort. SGLang/RadixArk, NVIDIA Dynamo, LMCache/TensorMesh, and other infrastructure efforts already address important parts of inference scheduling, caching, and data movement.

Project Seer should own a different layer: the long-lived agent execution graph and the future resource demand exposed by agent semantics. Existing inference systems can become backends or integration partners. A useful internal rule is: if the core contribution could simply be a small SGLang feature or PR, it is probably not the differentiated research thesis.

# 11. Immediate Next Step

Start with workload characterization and an oracle simulation. The first deliverable should answer one question clearly: How much cheaper or more efficient could agent computing become if the runtime knew what the agent program was going to do next?

If the answer is “not much,” stop or fold the insights into existing systems. If the answer is “a lot,” Project Seer has the foundation for a new research area—and potentially a new infrastructure company.