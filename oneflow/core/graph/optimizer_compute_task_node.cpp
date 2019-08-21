#include "oneflow/core/graph/logical_node.h"
#include "oneflow/core/graph/optimizer_compute_task_node.h"

namespace oneflow {

void OptimizerCompTaskNode::ConsumeAllRegsts() {
  ForEachInDataEdge([&](TaskEdge* edge) { ConsumeRegst("in", edge->GetSoleRegst()); });
}

void OptimizerCompTaskNode::ProduceAllRegstsAndBindEdges() {
  ProduceRegst("data_tmp", false, 1, 1);
}

void OptimizerCompTaskNode::BuildExecGphAndRegst() {
  ExecNode* node = mut_exec_gph().NewNode();
  std::shared_ptr<Operator> sole_op = this->logical_node()->SoleOp();
  node->mut_op() = sole_op;
  const std::list<std::shared_ptr<RegstDesc>>& in_regsts = GetConsumedRegst("in");
  for (const auto& ibn : node->op()->input_bns()) {
    node->BindBnWithOneOfTheRegsts(ibn, in_regsts);
  }
  node->AddBnToRegstAndBindIt(&Operator::data_tmp_bns, GetProducedRegst("data_tmp"));
  node->InferBlobDescs(parallel_ctx());
}

void OptimizerCompTaskNode::InferProducedDataRegstTimeShape() {
  ForEachProducedDataRegst([](const std::string& name, RegstDesc* regst) {
    regst->mut_data_regst_time_shape()->reset(new Shape({Global<JobDesc>::Get()->TotalBatchNum()}));
  });
}

void OptimizerCompTaskNode::GenerateNonCtrlRegstHandlerProto(TaskProto* task_proto) const {
  RegstHandlerProto naive_proto = CreateRegstHandlerProto("Naive");
  ForEachNonCtrlConsumedRegstDescId([&](int64_t regst_desc_id) {
    naive_proto.mutable_consumed_regst_desc_ids()->add_regst_desc_id(regst_desc_id);
  });
  ForEachNonCtrlProducedRegstDescId([&](int64_t regst_desc_id) {
    naive_proto.mutable_produced_regst_desc_ids()->add_regst_desc_id(regst_desc_id);
  });
  if (!IsRegstHandlerProtoEmpty(naive_proto)) {
    *(task_proto->mutable_regst_handlers()->Add()) = naive_proto;
  }
}

}  // namespace oneflow
