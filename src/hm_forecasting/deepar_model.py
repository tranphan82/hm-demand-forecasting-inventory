from gluonts.dataset.common import ListDataset
from gluonts.torch.distributions import NegativeBinomialOutput
from gluonts.torch.model.deepar import DeepAREstimator
from lightning.pytorch import seed_everything


def train_deepar(
    series,
    prediction_length=28,
    context_length=56,
    max_epochs=5,
    num_batches_per_epoch=50,
    num_parallel_samples=200,
    seed=42,
):
    seed_everything(seed)
    estimator = DeepAREstimator(
        freq="D",
        prediction_length=prediction_length,
        context_length=context_length,
        distr_output=NegativeBinomialOutput(),
        num_parallel_samples=num_parallel_samples,
        num_batches_per_epoch=num_batches_per_epoch,
        trainer_kwargs={"max_epochs": max_epochs, "accelerator": "cpu"},
    )
    return estimator.train(ListDataset(series, freq="D"))


def forecast_samples(predictor, series):
    forecasts = predictor.predict(ListDataset(series, freq="D"))
    return {forecast.item_id: forecast.samples for forecast in forecasts}