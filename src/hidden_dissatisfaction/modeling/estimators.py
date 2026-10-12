"""Candidate estimator pipelines whose preprocessing is fitted within each fold."""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

from hidden_dissatisfaction.modeling.schema import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)


class PrevalenceClassifier(ClassifierMixin, BaseEstimator):
    """Constant-probability baseline learned only from the training labels."""

    prevalence_: float
    classes_: np.ndarray

    def fit(self, X: object, y: object) -> PrevalenceClassifier:
        """Learn training prevalence."""
        values = np.asarray(y, dtype=float)
        self.prevalence_ = float(values.mean())
        self.classes_ = np.asarray([0, 1])
        return self

    def predict_proba(self, X: object) -> np.ndarray:
        """Return the training prevalence for every sample."""
        count = len(X)  # type: ignore[arg-type]
        positive = np.full(count, self.prevalence_)
        return np.column_stack((1.0 - positive, positive))

    def predict(self, X: object) -> np.ndarray:
        """Apply the conventional 0.5 threshold."""
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


def build_candidates(seed: int) -> dict[str, BaseEstimator]:
    """Construct deterministic baseline and candidate pipelines."""
    one_hot = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
                ),
                [*NUMERIC_FEATURES, *BINARY_FEATURES],
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("encode", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                [*CATEGORICAL_FEATURES],
            ),
        ]
    )
    tree_one_hot = ColumnTransformer(
        [
            (
                "numeric",
                SimpleImputer(strategy="median"),
                [*NUMERIC_FEATURES, *BINARY_FEATURES],
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("encode", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                [*CATEGORICAL_FEATURES],
            ),
        ]
    )
    ordinal = ColumnTransformer(
        [
            (
                "numeric",
                SimpleImputer(strategy="median"),
                [*NUMERIC_FEATURES, *BINARY_FEATURES],
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        (
                            "encode",
                            OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
                        ),
                    ]
                ),
                [*CATEGORICAL_FEATURES],
            ),
        ]
    )
    candidates: dict[str, BaseEstimator] = {
        "prevalence": PrevalenceClassifier(),
        "logistic_regression": Pipeline(
            [
                ("preprocess", one_hot),
                (
                    "model",
                    LogisticRegression(class_weight="balanced", max_iter=2_000, random_state=seed),
                ),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("preprocess", tree_one_hot),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=300,
                        min_samples_leaf=5,
                        class_weight="balanced_subsample",
                        n_jobs=-1,
                        random_state=seed,
                    ),
                ),
            ]
        ),
        "hist_gradient_boosting": Pipeline(
            [
                ("preprocess", ordinal),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        learning_rate=0.08,
                        max_iter=250,
                        max_leaf_nodes=31,
                        l2_regularization=1.0,
                        class_weight="balanced",
                        categorical_features=[False]
                        * (len(NUMERIC_FEATURES) + len(BINARY_FEATURES))
                        + [True] * len(CATEGORICAL_FEATURES),
                        random_state=seed,
                    ),
                ),
            ]
        ),
    }
    catboost = _build_catboost_candidate(seed)
    if catboost is not None:
        candidates["catboost"] = catboost
    return candidates


def _build_catboost_candidate(seed: int) -> BaseEstimator | None:
    """Build the optional native-categorical candidate when CatBoost is installed."""
    try:
        from catboost import CatBoostClassifier
    except ImportError:
        return None

    numeric_and_binary = [*NUMERIC_FEATURES, *BINARY_FEATURES]
    preprocess = ColumnTransformer(
        [
            ("numeric", SimpleImputer(strategy="median"), numeric_and_binary),
            (
                "categorical",
                SimpleImputer(strategy="most_frequent"),
                [*CATEGORICAL_FEATURES],
            ),
        ]
    )
    categorical_indices = list(
        range(len(numeric_and_binary), len(numeric_and_binary) + len(CATEGORICAL_FEATURES))
    )
    return Pipeline(
        [
            ("preprocess", preprocess),
            (
                "model",
                CatBoostClassifier(
                    iterations=500,
                    depth=6,
                    learning_rate=0.05,
                    loss_function="Logloss",
                    eval_metric="PRAUC",
                    auto_class_weights="Balanced",
                    cat_features=categorical_indices,
                    random_seed=seed,
                    verbose=False,
                    allow_writing_files=False,
                    thread_count=-1,
                ),
            ),
        ]
    )
