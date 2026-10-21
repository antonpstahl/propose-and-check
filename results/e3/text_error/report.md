# E3: the text-level error against T

Texts with at least one claim false against T (hedges excluded), Claude Haiku 5.5, outside the pilot datasets; 95% interval from a bootstrap over the datasets.

| source | tier | arm | texts | wrong vs T | low | high | claims false vs T | claims per text |
|---|---|---|---|---|---|---|---|---|
| as run, v2 | synthetic | off | 639 | 0.962 | 0.934 | 0.984 | 0.116 | 18.1 |
| as run, v2 | synthetic | on | 640 | 0.933 | 0.866 | 0.975 | 0.076 | 17.4 |
| as run, v3 | synthetic | off | 639 | 0.962 | 0.934 | 0.984 | 0.116 | 18.1 |
| as run, v3 | synthetic | on | 640 | 0.933 | 0.866 | 0.975 | 0.076 | 17.4 |
| rerun D74, v3 | plasmode | off | 359 | 1.0 | 1.0 | 1.0 | 0.162 | 16.5 |
| rerun D74, v3 | plasmode | on | 359 | 0.986 | 0.972 | 0.997 | 0.12 | 16.3 |
| rerun D74, v3 | synthetic | off | 636 | 0.561 | 0.486 | 0.645 | 0.061 | 17.1 |
| rerun D74, v3 | synthetic | on | 639 | 0.119 | 0.048 | 0.203 | 0.008 | 16.1 |
| rerun, v3 | plasmode | off | 358 | 0.989 | 0.975 | 1.0 | 0.166 | 16.2 |
| rerun, v3 | plasmode | on | 360 | 0.983 | 0.969 | 0.994 | 0.12 | 16.0 |
| rerun, v3 | synthetic | off | 636 | 0.558 | 0.485 | 0.638 | 0.061 | 17.0 |
| rerun, v3 | synthetic | on | 639 | 0.116 | 0.048 | 0.198 | 0.008 | 16.1 |


## By model and n

| source | tier | arm | model | n | texts | wrong vs T | low | high | claims false vs T | claims per text |
|---|---|---|---|---|---|---|---|---|---|---|
| as run, v2 | synthetic | off | EBM | 5000 | 160 | 0.938 | 0.838 | 0.994 | 0.146 | 17.4 |
| as run, v2 | synthetic | off | EBM | 50000 | 160 | 0.956 | 0.938 | 0.975 | 0.077 | 19.5 |
| as run, v2 | synthetic | off | XGB2 | 5000 | 160 | 0.994 | 0.981 | 1.0 | 0.155 | 16.9 |
| as run, v2 | synthetic | off | XGB2 | 50000 | 159 | 0.962 | 0.925 | 1.0 | 0.093 | 18.6 |
| as run, v2 | synthetic | on | EBM | 5000 | 160 | 0.863 | 0.625 | 1.0 | 0.093 | 16.3 |
| as run, v2 | synthetic | on | EBM | 50000 | 160 | 0.925 | 0.887 | 0.963 | 0.052 | 19.2 |
| as run, v2 | synthetic | on | XGB2 | 5000 | 160 | 0.981 | 0.956 | 1.0 | 0.101 | 16.0 |
| as run, v2 | synthetic | on | XGB2 | 50000 | 160 | 0.963 | 0.931 | 0.988 | 0.064 | 18.1 |
| as run, v3 | synthetic | off | EBM | 5000 | 160 | 0.938 | 0.838 | 0.994 | 0.146 | 17.4 |
| as run, v3 | synthetic | off | EBM | 50000 | 160 | 0.956 | 0.938 | 0.975 | 0.077 | 19.5 |
| as run, v3 | synthetic | off | XGB2 | 5000 | 160 | 0.994 | 0.981 | 1.0 | 0.155 | 16.9 |
| as run, v3 | synthetic | off | XGB2 | 50000 | 159 | 0.962 | 0.925 | 1.0 | 0.093 | 18.6 |
| as run, v3 | synthetic | on | EBM | 5000 | 160 | 0.863 | 0.625 | 1.0 | 0.093 | 16.3 |
| as run, v3 | synthetic | on | EBM | 50000 | 160 | 0.925 | 0.887 | 0.963 | 0.052 | 19.2 |
| as run, v3 | synthetic | on | XGB2 | 5000 | 160 | 0.981 | 0.956 | 1.0 | 0.101 | 16.0 |
| as run, v3 | synthetic | on | XGB2 | 50000 | 160 | 0.963 | 0.931 | 0.988 | 0.064 | 18.1 |
| rerun D74, v3 | plasmode | off | EBM | 5000 | 89 | 1.0 | 1.0 | 1.0 | 0.204 | 16.0 |
| rerun D74, v3 | plasmode | off | EBM | 30000 | 90 | 1.0 | 1.0 | 1.0 | 0.138 | 18.3 |
| rerun D74, v3 | plasmode | off | XGB2 | 5000 | 90 | 1.0 | 1.0 | 1.0 | 0.188 | 14.9 |
| rerun D74, v3 | plasmode | off | XGB2 | 30000 | 90 | 1.0 | 1.0 | 1.0 | 0.127 | 16.9 |
| rerun D74, v3 | plasmode | on | EBM | 5000 | 90 | 0.967 | 0.933 | 1.0 | 0.137 | 15.3 |
| rerun D74, v3 | plasmode | on | EBM | 30000 | 89 | 1.0 | 1.0 | 1.0 | 0.117 | 18.3 |
| rerun D74, v3 | plasmode | on | XGB2 | 5000 | 90 | 0.989 | 0.967 | 1.0 | 0.121 | 14.6 |
| rerun D74, v3 | plasmode | on | XGB2 | 30000 | 90 | 0.989 | 0.967 | 1.0 | 0.105 | 17.0 |
| rerun D74, v3 | synthetic | off | EBM | 5000 | 159 | 0.648 | 0.544 | 0.766 | 0.076 | 16.4 |
| rerun D74, v3 | synthetic | off | EBM | 50000 | 159 | 0.447 | 0.316 | 0.597 | 0.035 | 17.6 |
| rerun D74, v3 | synthetic | off | XGB2 | 5000 | 160 | 0.688 | 0.588 | 0.794 | 0.09 | 16.8 |
| rerun D74, v3 | synthetic | off | XGB2 | 50000 | 158 | 0.462 | 0.369 | 0.548 | 0.044 | 17.5 |
| rerun D74, v3 | synthetic | on | EBM | 5000 | 160 | 0.144 | 0.019 | 0.356 | 0.01 | 15.4 |
| rerun D74, v3 | synthetic | on | EBM | 50000 | 159 | 0.094 | 0.013 | 0.228 | 0.006 | 16.6 |
| rerun D74, v3 | synthetic | on | XGB2 | 5000 | 160 | 0.144 | 0.013 | 0.381 | 0.01 | 15.7 |
| rerun D74, v3 | synthetic | on | XGB2 | 50000 | 160 | 0.094 | 0.0 | 0.206 | 0.007 | 16.6 |
| rerun, v3 | plasmode | off | EBM | 5000 | 90 | 1.0 | 1.0 | 1.0 | 0.209 | 15.8 |
| rerun, v3 | plasmode | off | EBM | 30000 | 90 | 0.989 | 0.967 | 1.0 | 0.13 | 18.0 |
| rerun, v3 | plasmode | off | XGB2 | 5000 | 88 | 0.989 | 0.966 | 1.0 | 0.192 | 14.3 |
| rerun, v3 | plasmode | off | XGB2 | 30000 | 90 | 0.978 | 0.944 | 1.0 | 0.143 | 16.8 |
| rerun, v3 | plasmode | on | EBM | 5000 | 90 | 0.978 | 0.944 | 1.0 | 0.136 | 14.8 |
| rerun, v3 | plasmode | on | EBM | 30000 | 90 | 0.978 | 0.944 | 1.0 | 0.111 | 18.6 |
| rerun, v3 | plasmode | on | XGB2 | 5000 | 90 | 1.0 | 1.0 | 1.0 | 0.126 | 14.1 |
| rerun, v3 | plasmode | on | XGB2 | 30000 | 90 | 0.978 | 0.944 | 1.0 | 0.111 | 16.6 |
| rerun, v3 | synthetic | off | EBM | 5000 | 159 | 0.648 | 0.544 | 0.766 | 0.076 | 16.4 |
| rerun, v3 | synthetic | off | EBM | 50000 | 159 | 0.447 | 0.316 | 0.597 | 0.035 | 17.6 |
| rerun, v3 | synthetic | off | XGB2 | 5000 | 160 | 0.675 | 0.569 | 0.794 | 0.089 | 16.6 |
| rerun, v3 | synthetic | off | XGB2 | 50000 | 158 | 0.462 | 0.369 | 0.548 | 0.044 | 17.5 |
| rerun, v3 | synthetic | on | EBM | 5000 | 160 | 0.144 | 0.019 | 0.356 | 0.01 | 15.4 |
| rerun, v3 | synthetic | on | EBM | 50000 | 159 | 0.094 | 0.013 | 0.228 | 0.006 | 16.6 |
| rerun, v3 | synthetic | on | XGB2 | 5000 | 160 | 0.131 | 0.006 | 0.369 | 0.009 | 15.7 |
| rerun, v3 | synthetic | on | XGB2 | 50000 | 160 | 0.094 | 0.0 | 0.206 | 0.007 | 16.6 |


## By claim form

| source | tier | arm | form | texts with one | false claims | of all false claims |
|---|---|---|---|---|---|---|
| as run, v2 | synthetic | off | direction, strict | 0.814 | 520 | 0.387 |
| as run, v2 | synthetic | off | threshold | 0.372 | 271 | 0.202 |
| as run, v2 | synthetic | off | negligible | 0.3 | 197 | 0.147 |
| as run, v2 | synthetic | off | strength, set | 0.166 | 119 | 0.089 |
| as run, v2 | synthetic | off | share | 0.08 | 54 | 0.04 |
| as run, v2 | synthetic | off | interaction, none | 0.078 | 50 | 0.037 |
| as run, v2 | synthetic | off | interaction, amplification | 0.058 | 40 | 0.03 |
| as run, v2 | synthetic | off | strength | 0.036 | 24 | 0.018 |
| as run, v2 | synthetic | off | rank, set | 0.02 | 17 | 0.013 |
| as run, v2 | synthetic | off | direction, set (generally) | 0.02 | 13 | 0.01 |
| as run, v2 | synthetic | off | interaction, sign_flip | 0.02 | 13 | 0.01 |
| as run, v2 | synthetic | off | peak | 0.013 | 8 | 0.006 |
| as run, v2 | synthetic | off | comparison | 0.006 | 7 | 0.005 |
| as run, v2 | synthetic | off | direction, mostly | 0.011 | 7 | 0.005 |
| as run, v2 | synthetic | off | rank | 0.005 | 3 | 0.002 |
| as run, v2 | synthetic | on | direction, strict | 0.883 | 565 | 0.667 |
| as run, v2 | synthetic | on | negligible | 0.297 | 190 | 0.224 |
| as run, v2 | synthetic | on | interaction, none | 0.041 | 26 | 0.031 |
| as run, v2 | synthetic | on | strength, set | 0.033 | 21 | 0.025 |
| as run, v2 | synthetic | on | share | 0.022 | 16 | 0.019 |
| as run, v2 | synthetic | on | interaction, amplification | 0.017 | 11 | 0.013 |
| as run, v2 | synthetic | on | threshold | 0.016 | 11 | 0.013 |
| as run, v2 | synthetic | on | rank, set | 0.005 | 3 | 0.004 |
| as run, v2 | synthetic | on | direction, mostly | 0.003 | 2 | 0.002 |
| as run, v2 | synthetic | on | direction, set (generally) | 0.002 | 1 | 0.001 |
| as run, v2 | synthetic | on | peak | 0.002 | 1 | 0.001 |
| as run, v3 | synthetic | off | direction, strict | 0.814 | 520 | 0.387 |
| as run, v3 | synthetic | off | threshold | 0.372 | 271 | 0.202 |
| as run, v3 | synthetic | off | negligible | 0.3 | 197 | 0.147 |
| as run, v3 | synthetic | off | strength, set | 0.166 | 119 | 0.089 |
| as run, v3 | synthetic | off | share | 0.08 | 54 | 0.04 |
| as run, v3 | synthetic | off | interaction, none | 0.078 | 50 | 0.037 |
| as run, v3 | synthetic | off | interaction, amplification | 0.058 | 40 | 0.03 |
| as run, v3 | synthetic | off | strength | 0.036 | 24 | 0.018 |
| as run, v3 | synthetic | off | rank, set | 0.02 | 17 | 0.013 |
| as run, v3 | synthetic | off | direction, set (generally) | 0.02 | 13 | 0.01 |
| as run, v3 | synthetic | off | interaction, sign_flip | 0.02 | 13 | 0.01 |
| as run, v3 | synthetic | off | peak | 0.013 | 8 | 0.006 |
| as run, v3 | synthetic | off | comparison | 0.006 | 7 | 0.005 |
| as run, v3 | synthetic | off | direction, mostly | 0.011 | 7 | 0.005 |
| as run, v3 | synthetic | off | rank | 0.005 | 3 | 0.002 |
| as run, v3 | synthetic | on | direction, strict | 0.883 | 565 | 0.667 |
| as run, v3 | synthetic | on | negligible | 0.297 | 190 | 0.224 |
| as run, v3 | synthetic | on | interaction, none | 0.041 | 26 | 0.031 |
| as run, v3 | synthetic | on | strength, set | 0.033 | 21 | 0.025 |
| as run, v3 | synthetic | on | share | 0.022 | 16 | 0.019 |
| as run, v3 | synthetic | on | interaction, amplification | 0.017 | 11 | 0.013 |
| as run, v3 | synthetic | on | threshold | 0.016 | 11 | 0.013 |
| as run, v3 | synthetic | on | rank, set | 0.005 | 3 | 0.004 |
| as run, v3 | synthetic | on | direction, mostly | 0.003 | 2 | 0.002 |
| as run, v3 | synthetic | on | direction, set (generally) | 0.002 | 1 | 0.001 |
| as run, v3 | synthetic | on | peak | 0.002 | 1 | 0.001 |
| rerun D74, v3 | plasmode | off | direction, set (generally) | 0.836 | 348 | 0.361 |
| rerun D74, v3 | plasmode | off | threshold | 0.443 | 172 | 0.178 |
| rerun D74, v3 | plasmode | off | strength, set | 0.24 | 109 | 0.113 |
| rerun D74, v3 | plasmode | off | direction, strict | 0.217 | 79 | 0.082 |
| rerun D74, v3 | plasmode | off | rank, set | 0.167 | 72 | 0.075 |
| rerun D74, v3 | plasmode | off | negligible | 0.131 | 54 | 0.056 |
| rerun D74, v3 | plasmode | off | interaction, amplification | 0.106 | 38 | 0.039 |
| rerun D74, v3 | plasmode | off | interaction, none | 0.053 | 19 | 0.02 |
| rerun D74, v3 | plasmode | off | share | 0.053 | 19 | 0.02 |
| rerun D74, v3 | plasmode | off | strength | 0.045 | 19 | 0.02 |
| rerun D74, v3 | plasmode | off | comparison | 0.025 | 9 | 0.009 |
| rerun D74, v3 | plasmode | off | drop | 0.025 | 9 | 0.009 |
| rerun D74, v3 | plasmode | off | direction, mostly | 0.017 | 6 | 0.006 |
| rerun D74, v3 | plasmode | off | interaction, sign_flip | 0.014 | 5 | 0.005 |
| rerun D74, v3 | plasmode | off | peak | 0.014 | 5 | 0.005 |
| rerun D74, v3 | plasmode | off | rank | 0.003 | 1 | 0.001 |
| rerun D74, v3 | plasmode | on | direction, set (generally) | 0.897 | 413 | 0.59 |
| rerun D74, v3 | plasmode | on | threshold | 0.415 | 149 | 0.213 |
| rerun D74, v3 | plasmode | on | rank, set | 0.092 | 42 | 0.06 |
| rerun D74, v3 | plasmode | on | strength, set | 0.103 | 37 | 0.053 |
| rerun D74, v3 | plasmode | on | strength | 0.028 | 20 | 0.029 |
| rerun D74, v3 | plasmode | on | direction, mostly | 0.036 | 13 | 0.019 |
| rerun D74, v3 | plasmode | on | direction, strict | 0.033 | 12 | 0.017 |
| rerun D74, v3 | plasmode | on | interaction, none | 0.022 | 8 | 0.011 |
| rerun D74, v3 | plasmode | on | comparison | 0.017 | 6 | 0.009 |
| rerun D74, v3 | synthetic | off | threshold | 0.253 | 167 | 0.254 |
| rerun D74, v3 | synthetic | off | strength, set | 0.182 | 143 | 0.217 |
| rerun D74, v3 | synthetic | off | negligible | 0.112 | 75 | 0.114 |
| rerun D74, v3 | synthetic | off | direction, strict | 0.112 | 71 | 0.108 |
| rerun D74, v3 | synthetic | off | strength | 0.066 | 45 | 0.068 |
| rerun D74, v3 | synthetic | off | share | 0.055 | 38 | 0.058 |
| rerun D74, v3 | synthetic | off | interaction, amplification | 0.044 | 29 | 0.044 |
| rerun D74, v3 | synthetic | off | interaction, none | 0.038 | 24 | 0.036 |
| rerun D74, v3 | synthetic | off | rank, set | 0.033 | 23 | 0.035 |
| rerun D74, v3 | synthetic | off | interaction, sign_flip | 0.027 | 17 | 0.026 |
| rerun D74, v3 | synthetic | off | peak | 0.022 | 14 | 0.021 |
| rerun D74, v3 | synthetic | off | drop | 0.011 | 7 | 0.011 |
| rerun D74, v3 | synthetic | off | comparison | 0.005 | 3 | 0.005 |
| rerun D74, v3 | synthetic | off | direction, mostly | 0.003 | 2 | 0.003 |
| rerun D74, v3 | synthetic | on | strength, set | 0.028 | 20 | 0.244 |
| rerun D74, v3 | synthetic | on | negligible | 0.03 | 19 | 0.232 |
| rerun D74, v3 | synthetic | on | interaction, none | 0.019 | 12 | 0.146 |
| rerun D74, v3 | synthetic | on | share | 0.013 | 11 | 0.134 |
| rerun D74, v3 | synthetic | on | interaction, amplification | 0.013 | 8 | 0.098 |
| rerun D74, v3 | synthetic | on | peak | 0.005 | 3 | 0.037 |
| rerun D74, v3 | synthetic | on | threshold | 0.005 | 3 | 0.037 |
| rerun D74, v3 | synthetic | on | comparison | 0.003 | 2 | 0.024 |
| rerun D74, v3 | synthetic | on | rank, set | 0.003 | 2 | 0.024 |
| rerun D74, v3 | synthetic | on | direction, mostly | 0.002 | 1 | 0.012 |
| rerun D74, v3 | synthetic | on | direction, strict | 0.002 | 1 | 0.012 |
| rerun, v3 | plasmode | off | direction, set (generally) | 0.844 | 350 | 0.363 |
| rerun, v3 | plasmode | off | threshold | 0.531 | 211 | 0.219 |
| rerun, v3 | plasmode | off | strength, set | 0.249 | 101 | 0.105 |
| rerun, v3 | plasmode | off | direction, strict | 0.187 | 68 | 0.071 |
| rerun, v3 | plasmode | off | rank, set | 0.137 | 62 | 0.064 |
| rerun, v3 | plasmode | off | negligible | 0.128 | 60 | 0.062 |
| rerun, v3 | plasmode | off | interaction, amplification | 0.087 | 32 | 0.033 |
| rerun, v3 | plasmode | off | interaction, none | 0.061 | 22 | 0.023 |
| rerun, v3 | plasmode | off | drop | 0.036 | 13 | 0.013 |
| rerun, v3 | plasmode | off | share | 0.036 | 13 | 0.013 |
| rerun, v3 | plasmode | off | strength | 0.025 | 9 | 0.009 |
| rerun, v3 | plasmode | off | comparison | 0.022 | 8 | 0.008 |
| rerun, v3 | plasmode | off | direction, mostly | 0.017 | 6 | 0.006 |
| rerun, v3 | plasmode | off | peak | 0.014 | 5 | 0.005 |
| rerun, v3 | plasmode | off | interaction, sign_flip | 0.008 | 3 | 0.003 |
| rerun, v3 | plasmode | off | rank | 0.003 | 1 | 0.001 |
| rerun, v3 | plasmode | on | direction, set (generally) | 0.878 | 407 | 0.587 |
| rerun, v3 | plasmode | on | threshold | 0.431 | 157 | 0.227 |
| rerun, v3 | plasmode | on | strength, set | 0.1 | 36 | 0.052 |
| rerun, v3 | plasmode | on | rank, set | 0.069 | 34 | 0.049 |
| rerun, v3 | plasmode | on | strength | 0.028 | 20 | 0.029 |
| rerun, v3 | plasmode | on | direction, mostly | 0.039 | 14 | 0.02 |
| rerun, v3 | plasmode | on | direction, strict | 0.033 | 12 | 0.017 |
| rerun, v3 | plasmode | on | comparison | 0.019 | 7 | 0.01 |
| rerun, v3 | plasmode | on | interaction, none | 0.017 | 6 | 0.009 |
| rerun, v3 | synthetic | off | threshold | 0.252 | 166 | 0.253 |
| rerun, v3 | synthetic | off | strength, set | 0.182 | 143 | 0.218 |
| rerun, v3 | synthetic | off | negligible | 0.112 | 75 | 0.115 |
| rerun, v3 | synthetic | off | direction, strict | 0.112 | 71 | 0.108 |
| rerun, v3 | synthetic | off | strength | 0.066 | 45 | 0.069 |
| rerun, v3 | synthetic | off | share | 0.055 | 38 | 0.058 |
| rerun, v3 | synthetic | off | interaction, amplification | 0.042 | 28 | 0.043 |
| rerun, v3 | synthetic | off | interaction, none | 0.038 | 24 | 0.037 |
| rerun, v3 | synthetic | off | rank, set | 0.033 | 23 | 0.035 |
| rerun, v3 | synthetic | off | interaction, sign_flip | 0.027 | 17 | 0.026 |
| rerun, v3 | synthetic | off | peak | 0.02 | 13 | 0.02 |
| rerun, v3 | synthetic | off | drop | 0.011 | 7 | 0.011 |
| rerun, v3 | synthetic | off | comparison | 0.005 | 3 | 0.005 |
| rerun, v3 | synthetic | off | direction, mostly | 0.003 | 2 | 0.003 |
| rerun, v3 | synthetic | on | strength, set | 0.028 | 20 | 0.25 |
| rerun, v3 | synthetic | on | negligible | 0.03 | 19 | 0.237 |
| rerun, v3 | synthetic | on | interaction, none | 0.019 | 12 | 0.15 |
| rerun, v3 | synthetic | on | share | 0.011 | 10 | 0.125 |
| rerun, v3 | synthetic | on | interaction, amplification | 0.013 | 8 | 0.1 |
| rerun, v3 | synthetic | on | peak | 0.005 | 3 | 0.037 |
| rerun, v3 | synthetic | on | threshold | 0.005 | 3 | 0.037 |
| rerun, v3 | synthetic | on | comparison | 0.003 | 2 | 0.025 |
| rerun, v3 | synthetic | on | rank, set | 0.003 | 2 | 0.025 |
| rerun, v3 | synthetic | on | direction, mostly | 0.002 | 1 | 0.013 |


## The claims most often false against T

| source | tier | arm | dsl | texts |
|---|---|---|---|---|
| as run, v2 | synthetic | off | direction("history_months") == "decreasing" | 520 |
| as run, v2 | synthetic | off | negligible("n_inquiries") | 187 |
| as run, v2 | synthetic | off | strength("dti") in ("negligible", "weak") | 45 |
| as run, v2 | synthetic | off | interaction("utilization", "n_delinquencies", pattern="none") | 43 |
| as run, v2 | synthetic | off | strength("history_months") in ("negligible", "weak") | 43 |
| as run, v2 | synthetic | off | threshold("utilization", at=0.7) | 41 |
| as run, v2 | synthetic | off | threshold("n_delinquencies", at=2.0) | 28 |
| as run, v2 | synthetic | off | threshold("utilization", at=0.75) | 28 |
| as run, v2 | synthetic | on | direction("history_months") == "decreasing" | 565 |
| as run, v2 | synthetic | on | negligible("n_inquiries") | 189 |
| as run, v2 | synthetic | on | interaction("utilization", "n_delinquencies", pattern="none") | 22 |
| as run, v2 | synthetic | on | strength("age") in ("weak", "moderate") | 20 |
| as run, v2 | synthetic | on | share("utilization") == approx(0.35) | 11 |
| as run, v2 | synthetic | on | interaction("history_months", "n_inquiries", pattern="amplification") | 10 |
| as run, v2 | synthetic | on | threshold("n_delinquencies", at=2.0) | 5 |
| as run, v2 | synthetic | on | interaction("history_months", "n_inquiries", pattern="none") | 4 |
| as run, v3 | synthetic | off | direction("history_months") == "decreasing" | 520 |
| as run, v3 | synthetic | off | negligible("n_inquiries") | 187 |
| as run, v3 | synthetic | off | strength("dti") in ("negligible", "weak") | 45 |
| as run, v3 | synthetic | off | interaction("utilization", "n_delinquencies", pattern="none") | 43 |
| as run, v3 | synthetic | off | strength("history_months") in ("negligible", "weak") | 43 |
| as run, v3 | synthetic | off | threshold("utilization", at=0.7) | 41 |
| as run, v3 | synthetic | off | threshold("n_delinquencies", at=2.0) | 28 |
| as run, v3 | synthetic | off | threshold("utilization", at=0.75) | 28 |
| as run, v3 | synthetic | on | direction("history_months") == "decreasing" | 565 |
| as run, v3 | synthetic | on | negligible("n_inquiries") | 189 |
| as run, v3 | synthetic | on | interaction("utilization", "n_delinquencies", pattern="none") | 22 |
| as run, v3 | synthetic | on | strength("age") in ("weak", "moderate") | 20 |
| as run, v3 | synthetic | on | share("utilization") == approx(0.35) | 11 |
| as run, v3 | synthetic | on | interaction("history_months", "n_inquiries", pattern="amplification") | 10 |
| as run, v3 | synthetic | on | threshold("n_delinquencies", at=2.0) | 5 |
| as run, v3 | synthetic | on | interaction("history_months", "n_inquiries", pattern="none") | 4 |
| rerun D74, v3 | plasmode | off | direction("PAY_0") in ("increasing", "mostly_increasing") | 251 |
| rerun D74, v3 | plasmode | off | threshold("PAY_0", at=2.0) | 101 |
| rerun D74, v3 | plasmode | off | direction("PAY_0") == "increasing" | 77 |
| rerun D74, v3 | plasmode | off | direction("BILL_AMT2") in ("increasing", "mostly_increasing") | 58 |
| rerun D74, v3 | plasmode | off | strength("PAY_AMT2") in ("negligible", "weak") | 45 |
| rerun D74, v3 | plasmode | off | direction("LIMIT_BAL") in ("increasing", "mostly_increasing") | 38 |
| rerun D74, v3 | plasmode | off | threshold("PAY_0", at=1.5) | 36 |
| rerun D74, v3 | plasmode | off | strength("BILL_AMT1") in ("negligible", "weak") | 33 |
| rerun D74, v3 | plasmode | on | direction("PAY_0") in ("increasing", "mostly_increasing") | 271 |
| rerun D74, v3 | plasmode | on | direction("BILL_AMT2") in ("increasing", "mostly_increasing") | 115 |
| rerun D74, v3 | plasmode | on | threshold("PAY_0", at=2.0) | 82 |
| rerun D74, v3 | plasmode | on | threshold("PAY_0", at=1.5) | 66 |
| rerun D74, v3 | plasmode | on | direction("LIMIT_BAL") in ("increasing", "mostly_increasing") | 26 |
| rerun D74, v3 | plasmode | on | strength("BILL_AMT2") in ("weak", "moderate") | 20 |
| rerun D74, v3 | plasmode | on | strength("PAY_AMT2") in ("negligible", "weak") | 17 |
| rerun D74, v3 | plasmode | on | direction("PAY_0") == "increasing" | 12 |
| rerun D74, v3 | synthetic | off | direction("history_months") == "decreasing" | 71 |
| rerun D74, v3 | synthetic | off | negligible("n_inquiries") | 71 |
| rerun D74, v3 | synthetic | off | strength("dti") in ("negligible", "weak") | 57 |
| rerun D74, v3 | synthetic | off | strength("history_months") in ("negligible", "weak") | 53 |
| rerun D74, v3 | synthetic | off | threshold("utilization", at=0.6) | 28 |
| rerun D74, v3 | synthetic | off | threshold("utilization", at=0.7) | 28 |
| rerun D74, v3 | synthetic | off | strength("n_delinquencies") == "moderate" | 23 |
| rerun D74, v3 | synthetic | off | threshold("utilization", at=0.69) | 22 |
| rerun D74, v3 | synthetic | on | negligible("n_inquiries") | 19 |
| rerun D74, v3 | synthetic | on | strength("age") in ("weak", "moderate") | 18 |
| rerun D74, v3 | synthetic | on | interaction("utilization", "n_delinquencies", pattern="none") | 11 |
| rerun D74, v3 | synthetic | on | interaction("history_months", "n_inquiries", pattern="amplification") | 8 |
| rerun D74, v3 | synthetic | on | share("utilization") == approx(0.35) | 6 |
| rerun D74, v3 | synthetic | on | share("n_delinquencies") == approx(0.206) | 3 |
| rerun D74, v3 | synthetic | on | rank("noise_2") in (4, 5, 6, 7, 8) | 2 |
| rerun D74, v3 | synthetic | on | threshold("utilization", at=0.7) | 2 |
| rerun, v3 | plasmode | off | direction("PAY_0") in ("increasing", "mostly_increasing") | 261 |
| rerun, v3 | plasmode | off | threshold("PAY_0", at=2.0) | 115 |
| rerun, v3 | plasmode | off | direction("PAY_0") == "increasing" | 67 |
| rerun, v3 | plasmode | off | direction("BILL_AMT2") in ("increasing", "mostly_increasing") | 59 |
| rerun, v3 | plasmode | off | strength("PAY_AMT2") in ("negligible", "weak") | 39 |
| rerun, v3 | plasmode | off | threshold("PAY_0", at=1.5) | 35 |
| rerun, v3 | plasmode | off | strength("BILL_AMT1") in ("negligible", "weak") | 31 |
| rerun, v3 | plasmode | off | negligible("AGE") | 30 |
| rerun, v3 | plasmode | on | direction("PAY_0") in ("increasing", "mostly_increasing") | 276 |
| rerun, v3 | plasmode | on | direction("BILL_AMT2") in ("increasing", "mostly_increasing") | 112 |
| rerun, v3 | plasmode | on | threshold("PAY_0", at=2.0) | 87 |
| rerun, v3 | plasmode | on | threshold("PAY_0", at=1.5) | 68 |
| rerun, v3 | plasmode | on | strength("BILL_AMT2") in ("weak", "moderate") | 19 |
| rerun, v3 | plasmode | on | strength("PAY_AMT2") in ("negligible", "weak") | 17 |
| rerun, v3 | plasmode | on | direction("LIMIT_BAL") in ("increasing", "mostly_increasing") | 15 |
| rerun, v3 | plasmode | on | direction("PAY_0") == "increasing" | 12 |
| rerun, v3 | synthetic | off | direction("history_months") == "decreasing" | 71 |
| rerun, v3 | synthetic | off | negligible("n_inquiries") | 71 |
| rerun, v3 | synthetic | off | strength("dti") in ("negligible", "weak") | 57 |
| rerun, v3 | synthetic | off | strength("history_months") in ("negligible", "weak") | 53 |
| rerun, v3 | synthetic | off | threshold("utilization", at=0.6) | 28 |
| rerun, v3 | synthetic | off | threshold("utilization", at=0.7) | 28 |
| rerun, v3 | synthetic | off | strength("n_delinquencies") == "moderate" | 23 |
| rerun, v3 | synthetic | off | threshold("utilization", at=0.69) | 22 |
| rerun, v3 | synthetic | on | negligible("n_inquiries") | 19 |
| rerun, v3 | synthetic | on | strength("age") in ("weak", "moderate") | 18 |
| rerun, v3 | synthetic | on | interaction("utilization", "n_delinquencies", pattern="none") | 11 |
| rerun, v3 | synthetic | on | interaction("history_months", "n_inquiries", pattern="amplification") | 8 |
| rerun, v3 | synthetic | on | share("utilization") == approx(0.35) | 6 |
| rerun, v3 | synthetic | on | share("n_delinquencies") == approx(0.206) | 3 |
| rerun, v3 | synthetic | on | rank("noise_2") in (4, 5, 6, 7, 8) | 2 |
| rerun, v3 | synthetic | on | threshold("utilization", at=0.7) | 2 |

