#include "oneflow/core/record/ofrecord_jpeg_decoder.h"
#include "oneflow/core/record/image_preprocess.h"

namespace oneflow {

template<typename T>
int32_t OFRecordDecoderImpl<EncodeCase::kJpeg, T>::GetColNumOfFeature(
    const Feature& feature, int64_t one_col_elem_num) const {
  return feature.bytes_list().value_size();
}

template<typename T>
void OFRecordDecoderImpl<EncodeCase::kJpeg, T>::ReadOneCol(
    DeviceCtx* ctx, const Feature& feature, const BlobConf& blob_conf,
    int32_t col_id, T* out_dptr, int64_t one_col_elem_num) const {
  CHECK(feature.has_bytes_list());
  const std::string& src_data = feature.bytes_list().value(col_id);
  cv::_InputArray image_data(src_data.data(), src_data.size());
  cv::Mat image = cv::imdecode(image_data, cv::IMREAD_ANYCOLOR);
  CHECK(image.isContinuous());
  FOR_RANGE(size_t, i, 0, blob_conf.jpeg().preprocess_size()) {
    ImagePreprocessIf* preprocess =
        GetImagePreprocess(blob_conf.jpeg().preprocess(i).preprocess_case());
    preprocess->DoPreprocess(&image, blob_conf.jpeg().preprocess(i));
  }
  CHECK_EQ(blob_conf.shape().dim_size(), image.dims);
  FOR_RANGE(size_t, i, 0, image.dims) {
    CHECK_EQ(blob_conf.shape().dim(i), image.size[i]);
  }
  CopyElem(image.data, out_dptr, one_col_elem_num);
}

#define INSTANTIATE_OFRECORD_JPEG_DECODER(type_cpp, type_proto) \
  template class OFRecordDecoderImpl<EncodeCase::kJpeg, type_cpp>;

OF_PP_FOR_EACH_TUPLE(INSTANTIATE_OFRECORD_JPEG_DECODER,
                     ARITHMETIC_DATA_TYPE_SEQ)

}  // namespace oneflow
