-- Rename active registry benchmark terminology to replay terminology.
-- Historical migrations retain their original wording as audit evidence; the
-- active registry snapshot should expose only the current Replay names.

UPDATE trading_registry
SET id = replace(
          replace(
            replace(
              replace(
                replace(id, 'EVALBENCH', 'EVALREPLAY'),
                'EVALBMK',
                'EVALRPL'
              ),
              'STORBENCH',
              'STORRPL'
            ),
            'BENCH',
            'REPLAY'
          ),
          'BMK',
          'RPL'
        ),
    key = replace(replace(replace(key, 'BENCHMARK', 'REPLAY'), 'Benchmark', 'Replay'), 'benchmark', 'replay'),
    payload = replace(
                replace(
                  replace(
                    replace(
                      replace(
                        replace(replace(replace(payload, 'BENCHMARK', 'REPLAY'), 'Benchmark', 'Replay'), 'benchmark', 'replay'),
                        'replay_replay',
                        'replay'
                      ),
                      'promotion_replay_candidate_policy_replay',
                      'promotion_replay_candidate_policy'
                    ),
                    'candidate_policy_replay_replay',
                    'candidate_policy_replay'
                  ),
                  'model_specific_replay_downloads_ttl_delete_after_replay_close',
                  'model_specific_replay_downloads_ttl_delete_after_replay_close'
                ),
                'okx_history_candles_for_replay_windows',
                'okx_history_candles_for_replay_windows'
              ),
    path = replace(
             replace(
               replace(
                 replace(replace(replace(path, 'BENCHMARK', 'REPLAY'), 'Benchmark', 'Replay'), 'benchmark', 'replay'),
                 'replay_replay',
                 'replay'
               ),
               'promotion_replay_candidate_policy_replay',
               'promotion_replay_candidate_policy'
             ),
             'trading-evaluation/replays/promotion_replay_candidate_policy.json',
             'trading-evaluation/replays/promotion_replay_candidate_policy.json'
           ),
    applies_to = replace(
                   replace(
                     replace(
                       replace(replace(replace(applies_to, 'BENCHMARK', 'REPLAY'), 'Benchmark', 'Replay'), 'benchmark', 'replay'),
                       'replay_replay',
                       'replay'
                     ),
                     'candidate_policy_replay_replay',
                     'candidate_policy_replay'
                   ),
                   'promotion_replay',
                   'promotion_replay'
                 ),
    note = replace(
             replace(
               replace(
                 replace(
                   replace(
                     replace(replace(replace(note, 'BENCHMARK', 'REPLAY'), 'Benchmark', 'Replay'), 'benchmark', 'replay'),
                     'replay_replay',
                     'replay'
                   ),
                   'Promotion replay replay',
                   'Promotion replay'
                 ),
                 'promotion replay replay',
                 'promotion replay'
               ),
               'replay/replay',
               'replay'
             ),
             'candidate-policy replay replay',
             'candidate-policy replay'
           ),
    updated_at = NOW()
WHERE id ILIKE '%bench%'
   OR id ILIKE '%bmk%'
   OR key ILIKE '%benchmark%'
   OR payload ILIKE '%benchmark%'
   OR path ILIKE '%benchmark%'
   OR applies_to ILIKE '%benchmark%'
   OR note ILIKE '%benchmark%';
