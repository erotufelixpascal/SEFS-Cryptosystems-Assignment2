# Experiment results

Arms: manual, ai/run1, manual_extended. Faults scored in every arm: 20.

## Per arm

| arm | tests | faults_detected | mutation_score | score_95ci | line_coverage | branch_coverage | real_defects | false_positives | minutes | faults_per_hour | valid_findings_per_hour | ai_prompts | ai_tests_proposed | ai_accepted | ai_edited | ai_rejected | ai_review_minutes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| manual | 8 | 5/20 | 25.0% | 11.2%-46.9% | 70.9% | 47.1% | 0 | 5 | 160 | 1.88 | 1.88 |  |  |  |  |  |  |
| ai/run1 | 340 | 14/20 | 70.0% | 48.1%-85.5% | 87.7% | 77.3% | 0 | 1 | 50 | 16.80 | 16.80 | 5 | 132 | 131 | 1 | 0 | 50 |
| manual_extended | 5 | 0/20 | 0.0% | 0.0%-16.1% | 36.8% | 9.7% | 0 | 0 | 100 | 0.00 | 0.00 |  |  |  |  |  |  |

## manual vs each other arm

| comparison | faults | only_baseline | only_other_arm | both | neither | score_difference | diff_95ci_bootstrap | mcnemar_exact_p |
|---|---|---|---|---|---|---|---|---|
| ai/run1 vs manual | 20 | 0 | 9 | 5 | 6 | +45.0 pts | +25.0 to +65.0 pts | 0.0039 |
| manual_extended vs manual | 20 | 5 | 0 | 0 | 15 | -25.0 pts | -45.0 to -5.0 pts | 0.0625 |

McNemar's exact test uses only the faults one arm caught and the other missed. Bootstrap: 10000 paired resamples of faults, seed 2026.

## Detection by area

| area | faults | manual | ai/run1 | manual_extended |
|---|---|---|---|---|
| authentication | 5 | 0.0% | 80.0% | 0.0% |
| round_trip | 5 | 20.0% | 100.0% | 0.0% |
| chunk_boundaries | 5 | 60.0% | 60.0% | 0.0% |
| tamper | 5 | 20.0% | 40.0% | 0.0% |

## Per fault

| id | area | severity | description | manual | ai/run1 | manual_extended |
|---|---|---|---|---|---|---|
| M01_AUTH_allowed_characters | authentication | low | Non-ASCII letters and digits (such as é or full-width digits) are accepted in usernames and passwords, although the spec allows only ASCII | missed | detected | missed |
| M02_AUTH_password_check | authentication | high | Any password logs a user in, because the typed password's hash is compared with itself instead of with the stored hash | missed | detected | missed |
| M03_AUTH_change_password | authentication | high | A user's password can be changed without knowing the old password, as long as the new password is valid | missed | detected | missed |
| M04_AUTH_delete_or_change_line | authentication | medium | Deleting or changing a user also deletes or changes every user whose name starts with the same letters (removing "bob" also removes "bobby") | missed | missed | missed |
| M05_AUTH_file_owner_check | authentication | high | Any logged-in user can read, write or delete another user's files, because the ownership check no longer runs when an owner is given | missed | detected | missed |
| M06_ROUNDTRIP_read_returns_bytes | round_trip | medium | Reading from a file returns one byte too few, so the last requested byte is always missing | missed | detected | missed |
| M07_ROUNDTRIP_chunk_content_size | round_trip | medium | Reading a file returns extra padding bytes after the real data, because chunk content is no longer cut to its stored size | detected | detected | missed |
| M08_ROUNDTRIP_decrypt_writes_output | round_trip | medium | Decrypting a file whose plaintext ends with newline characters writes an output file with those newlines missing | missed | detected | missed |
| M09_ROUNDTRIP_text_to_bytes | round_trip | medium | Writing text that contains non-ASCII characters (such as é or emoji) silently drops those characters, so reading the file back gives different text | missed | detected | missed |
| M10_ROUNDTRIP_file_size_value | round_trip | medium | file_size reports one byte less than the file really holds | missed | detected | missed |
| M11_CHUNKS_split_into_1024_blocks | chunk_boundaries | high | The last byte of every 1,024-byte block is dropped when a file is split into chunks, so files longer than a few bytes are stored corrupted | detected | detected | missed |
| M12_CHUNKS_next_chunk_link | chunk_boundaries | medium | In a file with two or more chunks, the second-to-last chunk does not link to the last chunk, so multi-chunk files cannot be read back | detected | detected | missed |
| M13_CHUNKS_middle_chunks_full | chunk_boundaries | medium | A middle chunk that is shortened, or that links to the wrong next chunk, is accepted as long as the other condition still holds | missed | missed | missed |
| M14_CHUNKS_size_field_limit | chunk_boundaries | medium | A chunk whose size field has been changed to a value between 1,025 and 1,076 is accepted, so reading it returns header bytes as if they were file content | missed | missed | missed |
| M15_CHUNKS_old_chunks_deleted | chunk_boundaries | medium | When a file is rewritten, its old first chunk is never deleted, so stale chunk files (holding old data) pile up on disk | detected | detected | missed |
| M16_TAMPER_meta_digest_check | tamper | high | A meta file that has been altered is never detected, because the expected digest is compared with itself instead of with the computed one | missed | detected | missed |
| M17_TAMPER_start_end_names | tamper | medium | Every file with more than one chunk is wrongly reported as tampered, because the end name is compared with the first chunk instead of the last | detected | detected | missed |
| M18_TAMPER_sizes_add_up | tamper | medium | Extra data added to a file's chunks is not detected and is returned to the user, because the total only has to be at least the file size | missed | missed | missed |
| M19_TAMPER_chunk_file_length | tamper | medium | A chunk file with extra bytes appended to it is accepted, because only chunk files that are too short are rejected | missed | missed | missed |
| M20_TAMPER_padding_check | tamper | low | A change to the first padding byte straight after a chunk's content is not detected | missed | missed | missed |
