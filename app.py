import numpy as np
import pandas as pd
import streamlit as st
from functions import *
import matplotlib.pyplot as plt
import networkx as nx
import re
from networkx.exception import PowerIterationFailedConvergence

### Streamlit 구현
def main():
    st.sidebar.header("다운로드")
    st.title("산업연관데이터 DashBoard")
    mode = st.radio('모드 선택', ['Korea(2010~2020)', 'Korea(1990~2005)', 'Manual'])
    if mode == 'Korea(2010~2020)':
        first_idx = (6,2)
        subplus_edit =False
        number_of_label = 2
    elif mode == 'Korea(1990~2005)':
        first_idx = (5,2)
        subplus_edit =True
        number_of_label = 2
    else:
        first_idx = 0
        subplus_edit =False
        number_of_label = 2

    if 'number_of_divide' not in st.session_state:
        st.session_state['number_of_divide'] = 0

    if "ids_simbol" not in st.session_state:
        st.session_state.ids_simbol = {}

    if "show_edited" not in st.session_state:
        st.session_state.show_edited = False

    def _k(x):
        return int(x) if x.isdigit() else x

    def find_string_values(df, first_idx):
        # 특정 구간의 데이터 선택
        selected_df = df.iloc[first_idx[0]:, first_idx[1]:]

        # 문자열이 포함된 셀의 위치를 저장할 리스트
        string_locations = []

        # 모든 셀을 순회하며 문자열이 있는지 확인
        for row_idx, row in selected_df.iterrows():
            for col_idx, value in row.items():
                if isinstance(value, str):  # 문자열인지 확인
                    string_locations.append((row_idx, col_idx, value))

        return string_locations
    # 문자열이 포함된 위치를 NA로 대체하는 함수
    def replace_string_with_na(df, string_locations):
        for row_idx, col_idx, _ in string_locations:
            df.iloc[row_idx, col_idx] = np.nan  # 해당 위치의 값을 pd.NA로 대체

    def slice_until_first_non_nan_row(df):
        # DataFrame의 맨 아래부터 위로 순회하며 NaN이 아닌 첫 번째 행 찾기
        last_valid_index = None
        for row_idx in reversed(range(df.shape[0])):  # 아래에서 위로 순회
            if not df.iloc[row_idx].isna().all():  # NaN이 아닌 행을 찾으면
                last_valid_index = row_idx
                break

        # NaN이 아닌 행까지 슬라이싱 (찾지 못한 경우 전체 슬라이스)
        if last_valid_index is not None:
            sliced_df = df.iloc[:last_valid_index + 1]
        else:
            sliced_df = pd.DataFrame()  # 모든 행이 NaN인 경우 빈 DataFrame 반환

        return sliced_df, last_valid_index

    # 파일 업로드 섹션s
    st.session_state['uploaded_file'] = st.file_uploader("여기에 파일을 드래그하거나 클릭하여 업로드하세요.", type=['xls', 'xlsx'])
    if 'df' not in st.session_state:
        if st.session_state['uploaded_file']:
            st.write(st.session_state['uploaded_file'].name)
            st.session_state['df'] =load_data(st.session_state.uploaded_file)
            #st.session_state['df'].iloc[first_idx[0]:, first_idx[1]:].replace(' ', pd.NA, inplace=True)
            #st.session_state['df'].iloc[first_idx[0]:, first_idx[1]:].dropna(inplace = True)
            # 문자열이 포함된 위치 찾기
            string_values = find_string_values(st.session_state['df'], first_idx)
            # 문자열이 포함된 값을 NA로 대체
            replace_string_with_na(st.session_state['df'], string_values)
            # 사용 예시
            st.session_state['df'], last_valid_index = slice_until_first_non_nan_row(st.session_state['df'])
            st.write(string_values)
            st.session_state['mid_ID_idx'] = get_mid_ID_idx(st.session_state['df'], first_idx)
            st.session_state['df'].iloc[first_idx[0]:, first_idx[1]:] = st.session_state['df'].iloc[first_idx[0]:, first_idx[1]:].apply(pd.to_numeric, errors='coerce')
            if subplus_edit:
                st.session_state['df']=st.session_state['df'].iloc[:-1]

    if 'df' in st.session_state:
        uploaded_matrix_X = get_submatrix_withlabel(st.session_state['df'], first_idx[0], first_idx[1], st.session_state['mid_ID_idx'][0], st.session_state['mid_ID_idx'][1], first_idx, numberoflabel=number_of_label)
        uploaded_matrix_R = get_submatrix_withlabel(st.session_state['df'], st.session_state['mid_ID_idx'][0]+1, first_idx[1], st.session_state['df'].shape[0]-1, st.session_state['mid_ID_idx'][1], first_idx, numberoflabel=number_of_label)
        uploaded_matrix_C = get_submatrix_withlabel(st.session_state['df'], first_idx[0], st.session_state['mid_ID_idx'][1]+1, st.session_state['mid_ID_idx'][0], st.session_state['df'].shape[1]-1, first_idx, numberoflabel=number_of_label)

        uploaed_files = {
        "uploaded_df": st.session_state['df'],
        "uploaded_matrix_X": uploaded_matrix_X,
        "uploaded_matrix_R": uploaded_matrix_R,
        "uploaded_matrix_C": uploaded_matrix_C
                                }
        with st.sidebar.expander("최초 업로드 원본 파일"):
            download_multiple_csvs_as_zip(uploaed_files, zip_name="최초 업로드 원본 파일 전체(zip)")
            donwload_data(st.session_state['df'], 'uploaded_df')
            donwload_data(uploaded_matrix_X, 'uploaded_matrix_X')
            donwload_data(uploaded_matrix_R, 'uploaded_matrix_R')
            donwload_data(uploaded_matrix_C, 'uploaded_matrix_C')
        # 원본 부분 header 표시
        st.header('최초 업로드 된 Excel파일 입니다.')
        # 데이터프레임 표시 
        tab1, tab2, tab3, tab4 = st.tabs(['uploaded_df', 'uploaded_matrix_X', 'uploaded_matrix_R', 'uploaded_matrix_C'])
        with tab1:
            st.write(st.session_state['df'])
        with tab2:
            st.write(uploaded_matrix_X)
        with tab3:
            st.write(uploaded_matrix_R)
        with tab4:
            st.write(uploaded_matrix_C)

        if 'df_editing' not in st.session_state:
            st.session_state['df_editing'] = st.session_state['df'].copy()
            col = first_idx[1] - number_of_label                 # 라벨 열 위치
            s   = st.session_state['df_editing'].iloc[:, col]    # 해당 열 Series

            # ── ① float64 → Int64(정수, NaN 허용) ─────────────────────────────
            if pd.api.types.is_float_dtype(s):
                s = s.astype('Int64')        # 1.0 → 1,  NaN 그대로 유지
                s = s.astype('string')        # 1.0 → 1,  NaN 그대로 유지
                st.session_state['df_editing'].iloc[:, col] = s.astype('object') 

    if 'data_editing_log' not in st.session_state:
        st.session_state['data_editing_log'] = ''

    if 'df_editing' in st.session_state:
        st.header("DataFrame을 수정합니다.")
        st.markdown("#### 자동 입력 처리 (엑셀 파일로 일괄 처리)")
        
        # =========================
        # Batch Processing (업로드 즉시 준비 -> 텍스트 미리보기 -> 적용 버튼)
        # =========================
        alpha_file = st.file_uploader("Alpha 값 엑셀/ZIP 파일 업로드", type=["xlsx", "xls", "zip"])

        if alpha_file:
            # 원본 업로드 파일명(확장자 제외) - ZIP 매칭에만 사용
            original_filename_no_ext = st.session_state["uploaded_file"].name.rsplit(".", 1)[0]

            # 업로드 파일 변경 감지 (rerun에서도 중복 준비 방지)
            alpha_key = (alpha_file.name, len(alpha_file.getvalue()))
            if st.session_state.get("alpha_key") != alpha_key:
                st.session_state["alpha_key"] = alpha_key

                # 업로드 즉시 1단계+2단계 자동 수행
                try:
                    batch_df_clean, meta, preview_lines, summary_lines = prepare_batch_preview(
                        alpha_file, original_filename_no_ext
                    )
                    st.session_state["batch_df_clean"] = batch_df_clean
                    st.session_state["batch_meta"] = meta
                    st.session_state["batch_preview_lines"] = preview_lines
                except Exception as e:
                    st.session_state["batch_df_clean"] = None
                    st.error(f"미리보기 준비 중 오류: {e}")

            # --- 2단계: 텍스트 미리보기 출력 ---
            if st.session_state.get("batch_df_clean") is not None:
                st.markdown("##### 일괄 적용 내역 요약")
                df_prev = st.session_state["batch_df_clean"].copy()
                df_prev["from"] = df_prev["from"].astype(str)
                df_prev["to"]   = df_prev["to"].astype(str)
                df_prev["to_name"] = df_prev["to_name"].astype(str).replace("nan", "").fillna("")

                # to -> from 순 정렬 ( _k는 위에서 정의/이동된 함수 사용 )
                df_prev = df_prev.sort_values(by=["to", "from"], key=lambda s: s.map(_k))

                # to별 그룹 출력 (그룹키는 to 코드로 유지)
                for idx, (to_code, g) in enumerate(df_prev.groupby("to", sort=False), start=1):
                    # ✅ 표시용 이름: 그룹 내 to_name 고유값
                    names = [n for n in g["to_name"].dropna().unique().tolist() if n and n != "None"]
                    if len(names) == 0:
                        display_name = to_code
                    elif len(names) == 1:
                        display_name = names[0]
                    else:
                        display_name = f"{names[0]} 외 {len(names)-1}"

                    st.markdown(f"**[{idx}: {display_name}]**")

                    lines = [
                        f"{r['from']} -> {r['to']} : {float(r['alpha'])*100:.4f}%"
                        for _, r in g.iterrows()
                    ]
                    for i in range(0, len(lines), 5):
                        st.write(" | ".join(lines[i:i+5]))




                # --- 3단계: 적용 버튼 누르면 실제 업데이트 실행 ---
                if st.button("일괄 적용"):
                    try:
                        batch_df = st.session_state["batch_df_clean"]

                        df_curr = st.session_state["df_editing"]
                        code_col_idx = first_idx[1] - number_of_label

                        # -------------------------
                        # [NEW] 1) to/to_name 기반 자동 산업 추가 단계
                        # -------------------------
                        # (to, to_name) 중복 제거해서 한 번만 추가 시도
                        targets = batch_df[["to", "to_name"]].drop_duplicates()

                        for _, t in targets.iterrows():
                            new_code = str(t["to"])
                            new_name = str(t["to_name"]) if str(t["to_name"]) not in ["nan", "None"] else ""

                            # df에 해당 코드가 이미 있는지 확인
                            exists = (df_curr.iloc[:, code_col_idx].astype(str) == new_code).any()
                            if exists:
                                # 이미 있으면 ids_simbol에만 이름 보관(원하면 중복 방지 가능)
                                if new_code not in st.session_state.ids_simbol:
                                    st.session_state.ids_simbol[new_code] = []
                                if new_name and (new_name not in st.session_state.ids_simbol[new_code]):
                                    st.session_state.ids_simbol[new_code].append(new_name)
                                continue

                            # 없으면 "산업 추가" 버튼과 동일한 로직 실행
                            result = insert_row_and_col(
                                df_curr,
                                first_idx,
                                st.session_state["mid_ID_idx"],
                                new_code,
                                new_name if new_name else f"NEW_{new_code}",
                                number_of_label
                            )

                            df_curr, st.session_state["mid_ID_idx"] = result[0:2]
                            st.session_state["data_editing_log"] += (result[2] + "\n\n")

                            if new_code not in st.session_state.ids_simbol:
                                st.session_state.ids_simbol[new_code] = []
                            if new_name:
                                st.session_state.ids_simbol[new_code].append(new_name)

                        # 삽입 반영된 df를 다시 세션에 저장
                        st.session_state["df_editing"] = df_curr
                        df_curr = st.session_state["df_editing"]

                        grouped = batch_df.groupby("from")

                        df_curr = st.session_state["df_editing"]

                        # ✅ 기존 로직 유지 + number_of_label 반영
                        code_col_idx = first_idx[1] - number_of_label

                        log_msg = ""
                        for origin_code, group in grouped:
                            origin_indices = df_curr.index[df_curr.iloc[:, code_col_idx] == origin_code].tolist()
                            if len(origin_indices) != 1:
                                log_msg += f"Error: Origin Code '{origin_code}' 유일하지 않거나 없음. 스킵\n"
                                continue

                            origin_row_idx = origin_indices[0]
                            origin_col_idx = origin_row_idx - first_idx[0] + first_idx[1]

                            # snapshot
                            origin_row_data = df_curr.iloc[origin_row_idx, first_idx[1]:].copy()
                            origin_col_data = df_curr.iloc[first_idx[0]:, origin_col_idx].copy()

                            total_alpha = float(group["alpha"].sum())

                            # 타겟들에 동시 가산
                            for _, r in group.iterrows():
                                target_code = r["to"]
                                ratio = float(r["alpha"])

                                target_indices = df_curr.index[df_curr.iloc[:, code_col_idx] == target_code].tolist()
                                if len(target_indices) != 1:
                                    log_msg += f"Error: Target Code '{target_code}' 유일하지 않거나 없음. ({origin_code}->{target_code} 스킵)\n"
                                    continue

                                target_row_idx = target_indices[0]
                                target_col_idx = target_row_idx - first_idx[0] + first_idx[1]

                                df_curr.iloc[target_row_idx, first_idx[1]:] += origin_row_data * ratio
                                df_curr.iloc[first_idx[0]:, target_col_idx] += origin_col_data * ratio

                                log_msg += f"[Batch] {origin_code} -> {target_code}: {ratio*100:.2f}% 이동\n"

                            # origin 잔여 반영
                            remaining_ratio = 1.0 - total_alpha
                            if abs(remaining_ratio) < 1e-9:
                                remaining_ratio = 0.0

                            df_curr.iloc[origin_row_idx, first_idx[1]:] = origin_row_data * remaining_ratio
                            df_curr.iloc[first_idx[0]:, origin_col_idx] = origin_col_data * remaining_ratio
                            log_msg += f"\n[Batch Info] {origin_code} 잔여: {remaining_ratio*100:.4f}%\n\n"

                        st.session_state["df_editing"] = df_curr
                        st.session_state["data_editing_log"] += (log_msg + "\n")
                        st.session_state.show_edited = False
                        st.rerun()

                    except Exception as e:
                        st.error(f"처리 중 오류 발생: {e}")

        # Manual Processing (Existing)
        st.markdown("#### 수동 입력")
        col1, col2, col3 = st.columns(3)
        with col1:
            new_code = st.text_input('새로 삽입할 산업의 code를 입력하세요')
        with col2:
            name = st.text_input('새로 삽입할 산업의 이름을 입력하세요')
        with col3:
            if st.button('산업 추가'):
                result = insert_row_and_col(st.session_state['df_editing'], first_idx, st.session_state['mid_ID_idx'], new_code, name, number_of_label)
                st.session_state['df_editing'], st.session_state['mid_ID_idx'] = result[0:2]
                st.session_state['data_editing_log'] += (result[2] + '\n\n')
                if new_code not in st.session_state.ids_simbol:
                    st.session_state.ids_simbol[new_code] = []  # 새로운 리스트 생성
                st.session_state.ids_simbol[new_code].append(name)  # 값 추가
                st.session_state.show_edited = False
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            origin_code = st.text_input('from')
        with col2:
            target_code = st.text_input('to')
        with col3:
            alpha = float(st.text_input('alpha value (0.000 to 1.000)', '0.000'))
        with col4:
            if st.button('값 옮기기'):
                result = transfer_to_new_sector(st.session_state['df_editing'], first_idx, origin_code, target_code, alpha)
                st.session_state['df_editing'] = result[0]
                st.session_state['data_editing_log'] += (result[1] + '\n\n')
                st.session_state.show_edited = False
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button('0인 행(열) 삭제'):
                result = remove_zero_series(st.session_state['df_editing'], first_idx, st.session_state['mid_ID_idx'])
                st.session_state['df_editing'] = result[0]
                st.session_state['data_editing_log'] += (result[1] + '\n\n')
                st.session_state['mid_ID_idx'] = result[2]
                st.session_state.show_edited = False
        with col2:
             if st.button('-값 절반으로 줄이기'):
                mid_ID_idx_reduced = (st.session_state['mid_ID_idx'][0] - 1, st.session_state['mid_ID_idx'][1] - 1)
                result = reduce_negative_values(st.session_state['df_editing'], first_idx, mid_ID_idx_reduced)
                st.session_state['df_editing'] = result[0]
                st.session_state['data_editing_log'] += (result[1] + '\n\n')
                st.session_state['number_of_divide'] +=1
                st.session_state.show_edited = False
        with col3:
            if st.button('전체 적용'):
                st.session_state['df_edited'] = st.session_state['df_editing'].copy()
                st.session_state.show_edited = True
        st.markdown(f"##### - 값 나누는 것: **{st.session_state['number_of_divide']}** 번 적용")
        st.write(st.session_state['df_editing'])
    if 'df_edited' in st.session_state and st.session_state.show_edited:
        st.header('위에서 수정 된 Excel파일 입니다.')
        edited_matrix_X = get_submatrix_withlabel(st.session_state['df_edited'], first_idx[0],first_idx[1], st.session_state['mid_ID_idx'][0], st.session_state['mid_ID_idx'][1], first_idx, numberoflabel = 2)
        edited_matrix_R = get_submatrix_withlabel(st.session_state['df_edited'], st.session_state['mid_ID_idx'][0]+1,first_idx[1], st.session_state['df_edited'].shape[0]-1, st.session_state['mid_ID_idx'][1], first_idx, numberoflabel = 2)
        edited_matrix_C = get_submatrix_withlabel(st.session_state['df_edited'], first_idx[0], st.session_state['mid_ID_idx'][1]+1, st.session_state['mid_ID_idx'][0], st.session_state['df_edited'].shape[1]-1, first_idx, numberoflabel = 2)
        edited_files = {
        "edited_df": st.session_state['df_edited'],
        "edited_matrix_X": edited_matrix_X,
        "edited_matrix_R": edited_matrix_R,
        "edited_matrix_C": edited_matrix_C
                                }
        with st.sidebar.expander("수정된 파일"):
            download_multiple_csvs_as_zip(edited_files, zip_name="수정된 파일 전체(zip)")
            donwload_data(st.session_state['df_edited'], 'edited_df')
            donwload_data(edited_matrix_X, 'edited_matrix_X')
            donwload_data(edited_matrix_R, 'edited_matrix_R')
            donwload_data(edited_matrix_C, 'ueditedmatrix_C')
        # 데이터프레임 표시
        tab1, tab2, tab3, tab4 = st.tabs(['edited_df', 'edited_matrix_X', 'edited_matrix_R', 'edited_matrix_C'])

        with tab1:
            st.write(st.session_state['df_edited'])

        with tab2:
            st.write(edited_matrix_X)

        with tab3:
            st.write(edited_matrix_R)

        with tab4:
            st.write(edited_matrix_C)

    if 'df_edited' in st.session_state and st.session_state.show_edited:
        st.session_state['df_for_leontief'] = edited_matrix_X.iloc[:-1, :-1].copy()
        st.session_state['df_for_leontief'].index = range(st.session_state['df_for_leontief'].shape[0])
        st.session_state['df_for_leontief'].columns = range(st.session_state['df_for_leontief'].shape[1])

        st.session_state['df_for_r'] = edited_matrix_R.iloc[:-1, :-1].copy()
        st.session_state['df_for_r'].index = range(st.session_state['df_for_r'].shape[0])
        st.session_state['df_for_r'].columns = range(st.session_state['df_for_r'].shape[1])

        st.session_state['normalization_denominator'] = st.session_state['df_edited'].iloc[st.session_state['df_edited'].shape[0]-1, first_idx[1]:st.session_state['mid_ID_idx'][1]]
        st.session_state['normalization_denominator'] = pd.to_numeric(st.session_state['normalization_denominator'])
        st.session_state['normalization_denominator_replaced'] = st.session_state['normalization_denominator'].replace(0, np.finfo(float).eps)
        st.session_state['added_value_denominator'] = st.session_state['df_edited'].iloc[st.session_state['df_edited'].shape[0] - 2, first_idx[1]:st.session_state['mid_ID_idx'][1]]
        st.session_state['added_value_denominator'] = pd.to_numeric(st.session_state['added_value_denominator'])
        st.session_state['added_value_denominator_replaced'] = st.session_state['added_value_denominator'].replace(0, np.finfo(float).eps)

        st.session_state['added_value_denominator'] = st.session_state['df_edited'].iloc[st.session_state['df_edited'].shape[0] - 2, first_idx[1]:st.session_state['mid_ID_idx'][1]]
        st.session_state['added_value_denominator'] = pd.to_numeric(st.session_state['added_value_denominator'])
        st.session_state['added_value_denominator_replaced'] = st.session_state['added_value_denominator'].replace(0, np.finfo(float).eps)

        # 2025-12-26 추가
        st.session_state['v'] = (st.session_state['added_value_denominator'] / st.session_state['normalization_denominator_replaced'])

        v_vec = st.session_state['v'].to_numpy()
        V_matrix = np.diag(v_vec)
        st.session_state['V'] = V_matrix

        # 1) 두번째 행(= iloc[1])에서 '최종수요계' 찾기
        header2 = edited_matrix_C.iloc[1].fillna("").astype(str).str.strip()

        # 정확히 일치로 찾기
        pos = np.where(header2.values == "최종수요계")[0]
        if len(pos) == 0:
            # 혹시 공백/표기가 다른 경우 대비(부분일치)
            pos = np.where(header2.str.contains("최종수요", na=False).values)[0]

        if len(pos) == 0:
            raise ValueError("edited_matrix_C의 2번째 행에서 '최종수요계' 열을 못 찾았음")

        col_pos = int(pos[0])  # '최종수요계' 열의 '위치(정수)'

        # 2) 산업 행은 iloc[2:]부터 시작(라벨 2행 제거)
        st.session_state['y'] = pd.to_numeric(edited_matrix_C.iloc[2:, col_pos], errors="coerce").to_numpy().reshape(-1, 1)




        
    if 'df_for_leontief' in st.session_state and st.session_state.show_edited:
        st.session_state['df_for_leontief_with_label'] = st.session_state['df_for_leontief'].copy()
        st.session_state['df_for_leontief_without_label'] = st.session_state['df_for_leontief_with_label'].iloc[2:, 2:].copy()
        st.session_state['df_for_r_without_label'] = st.session_state['df_for_r'].iloc[2:, 2:].copy()
        st.session_state['df_for_r_with_label'] = st.session_state['df_for_r'].copy()
        
        tmp = st.session_state['df_for_leontief_without_label'].copy()
        tmp = tmp.apply(pd.to_numeric, errors='coerce')
        tmp = tmp.divide(st.session_state['normalization_denominator_replaced'], axis=1) ##d

        tmp2 = st.session_state['df_for_r_without_label'].copy()
        tmp2 = tmp2.apply(pd.to_numeric, errors='coerce')
        tmp2 = tmp2.divide(st.session_state['normalization_denominator_replaced'], axis=1) ##d
    
        st.session_state['df_for_leontief_with_label'].iloc[2:, 2:] = tmp
        st.session_state['df_for_r_with_label'].iloc[2:, 2:] = tmp2

        st.session_state['df_normalized_with_label'] = st.session_state['df_for_leontief_with_label'].copy()
        unit_matrix = np.eye(tmp.shape[0])
        subtracted_matrix = unit_matrix - tmp
        leontief = np.linalg.inv(subtracted_matrix.values)
        leontief = pd.DataFrame(leontief)
        # 현재 DataFrame을 가져오기
        current_df = st.session_state['df_for_leontief_with_label']

        # 기존 DataFrame에서 2행과 2열을 제거한 후, 크기를 정의
        existing_rows = current_df.shape[0] - 2  # 기존 DataFrame의 행 수
        existing_cols = current_df.shape[1] - 2  # 기존 DataFrame의 열 수

        # leontief 배열의 크기
        leontief_rows, leontief_cols = leontief.shape

        # 새로운 DataFrame 생성 (NaN으로 초기화)
        new_df = pd.DataFrame(np.nan, index=range(existing_rows + 1), columns=range(existing_cols + 1))

        # leontief 배열이 기존 크기와 일치할 때
        if leontief_rows == existing_rows and leontief_cols == existing_cols:
            # leontief 데이터를 새로운 DataFrame의 적절한 부분에 삽입
            new_df.iloc[:existing_rows, :existing_cols] = leontief  # 기존 데이터 부분에 할당

        # N*N 배열에서 N+1*N+1로 변환
        leontief_with_sums = np.zeros((leontief_rows + 1, leontief_cols + 1))
        leontief_with_sums[:-1, :-1] = leontief  # 기존 leontief 배열을 넣기
        leontief_with_sums[-1, :-1] = leontief.sum(axis=0)  # 마지막 행에 각 열의 합
        leontief_with_sums[:-1, -1] = leontief.sum(axis=1)  # 마지막 열에 각 행의 합

        # 마지막 행 값들을 마지막 행 평균으로 나누기
        last_row_mean = leontief_with_sums[-1, :-1].mean()  # 마지막 행 평균
        leontief_with_sums[-1, :-1] /= last_row_mean  # 마지막 행 나누기

        # 마지막 열 값들을 마지막 열 평균으로 나누기
        last_col_mean = leontief_with_sums[:-1, -1].mean()  # 마지막 열 평균
        leontief_with_sums[:-1, -1] /= last_col_mean  # 마지막 열 나누기

        # 최종적으로 N+1*N+1 배열을 새로운 DataFrame에 업데이트
        # 새로운 크기로 DataFrame을 초기화합니다.
        new_df = pd.DataFrame(leontief_with_sums)
        # 기존 DataFrame의 크기를 1씩 늘리기 (NaN으로 초기화)
        current_df = current_df.reindex(index=range(existing_rows + 3), 
                                        columns=range(existing_cols + 3))


        # 새로운 DataFrame을 기존 DataFrame의 적절한 위치에 업데이트
        current_df.iloc[2:2 + new_df.shape[0], 2:2 + new_df.shape[1]] = new_df
        current_df.iloc[1,-1]="FL"
        current_df.iloc[-1,1]="BL"
        # 세션 상태에 업데이트
        st.session_state['df_for_leontief_with_label'] = current_df


        ids_col = st.session_state['df_for_leontief_with_label'].iloc[1:-1, :2]
        fl_data = st.session_state['df_for_leontief_with_label'].iloc[1:-1, -1]
        bl_data = st.session_state['df_for_leontief_with_label'].iloc[-1, 1:-1]
        
        # DataFrame으로 변환 (bl_data가 Series일 경우 df로 변환 필요)
        fl_data = fl_data.to_frame(name="2")  # FL 열 이름 지정
        bl_data = bl_data.to_frame(name="3")  # BL 열 이름 지정

        # 인덱스를 리셋하여 병합이 가능하도록 정리
        ids_col = ids_col.reset_index(drop=True)
        fl_data = fl_data.reset_index(drop=True)
        bl_data = bl_data.reset_index(drop=True)

        # 좌우로 데이터프레임 결합 (concat 사용)
        st.session_state['fl_bl'] = pd.concat([ids_col, fl_data, bl_data], axis=1)

        st.session_state['df_for_leontief_with_label']=st.session_state['df_for_leontief_with_label'].iloc[:-1, :-1]
        st.session_state['df_for_leontief_without_label'] = st.session_state['df_for_leontief_with_label'].iloc[2:, 2:].copy()

        # 2025-12-26 추가 (GDP 및 부가가치 유발 효과)
        # L, y, V 준비
        L = st.session_state['df_for_leontief_without_label'].apply(pd.to_numeric, errors='coerce').fillna(0).to_numpy()

        y = np.asarray(st.session_state['y']).reshape(-1, 1)
        y = y[:-1, :] 

        V = st.session_state['V']
        v = np.asarray(st.session_state['v'], dtype=float).reshape(1, -1)


        # GDP 생성
        x = L @ y
        g = V @ x

        # 부가가치 유발 효과
        m_v = v @ L

        # =========================
        # [A] GDP(산업별 VA 유발액)
        # =========================
        base_df = st.session_state['df_for_leontief_with_label']

        ids_col = base_df.iloc[1:, :2].reset_index(drop=True)  # 라벨은 그대로(첫 라벨행 포함된 구조 유지)

        g_vec  = g.reshape(-1)
        g_data = pd.concat(
            [
                pd.DataFrame(["GDP"], columns=["2"]),
                pd.Series(g_vec).to_frame(name="2")
            ],
            axis=0
        ).reset_index(drop=True)

        st.session_state['gdp_by_industry'] = pd.concat([ids_col, g_data], axis=1)

        st.session_state['GDP_total'] = float(g_vec.sum())
        st.session_state['GDP_mean']  = float(g_vec.mean())



        # =========================
        # [B] 부가가치 유발효과(m_v)
        # =========================
        ids_col = base_df.iloc[1:, :2].reset_index(drop=True)

        mv_vec  = m_v.reshape(-1)
        mv_data = pd.concat(
            [
                pd.DataFrame(["부가가치유발효과"], columns=["2"]),
                pd.Series(mv_vec).to_frame(name="2")
            ],
            axis=0
        ).reset_index(drop=True)

        st.session_state['va_multiplier_by_sector'] = pd.concat([ids_col, mv_data], axis=1)

        st.session_state['m_v_total'] = float(mv_vec.sum())
        st.session_state['m_v_mean']  = float(mv_vec.mean())





        st.subheader('Leontief 과정 matrices')
        col1, col2, col3, col4, col5, col6, col7, col8, col9= st.tabs(['edited_df', 'normailization denominator', '투입계수행렬', 'leontief inverse','FL-BL','GDP','부가가치유발효과','부가가치계수행렬','부가가치계벡터'])
        with col1:
            st.write(st.session_state['df_for_leontief'])
        with col2:
            st.write(st.session_state['normalization_denominator'])
        with col3:
            st.write(st.session_state['df_normalized_with_label'])
        with col4:
            st.write(st.session_state['df_for_leontief_with_label'])
            invalid_positions = []
        with col5:
            st.write(st.session_state['fl_bl'])
        with col6:
            st.write(st.session_state['gdp_by_industry'])
            st.write("GDP_total (sum g):", st.session_state['GDP_total'])
            st.write("GDP_mean (mean g):", st.session_state['GDP_mean'])
        with col7:
            st.write(st.session_state['va_multiplier_by_sector'])
            st.write("m_v_total (sum m_v):", st.session_state['m_v_total'])
            st.write("m_v_mean (mean m_v):", st.session_state['m_v_mean'])
        with col8:
            st.write(st.session_state['df_for_r_with_label'])
        with col9:
            st.write(st.session_state['added_value_denominator'])

        st.subheader("레온티에프 역행렬을 통한 정합성 검증 내용")
        is_equal_to_one_row = np.isclose(leontief_with_sums[-1, :-1].mean(), 1)
        st.write(f"행(영향력계수) 합의 평균이 1과 동일 여부 {is_equal_to_one_row}")
        is_equal_to_one_row = np.isclose(leontief_with_sums[:-1, -1].mean(), 1)
        st.write(f"열(감응도계수) 합의 평균이 1과 동일 여부 {is_equal_to_one_row}")


        # 1. 행렬을 순회하며 -0.1 ~ 2 범위를 벗어난 값의 위치를 찾음
        for i in range(leontief.shape[0]):
            for j in range(leontief.shape[1]):
                value = leontief.iloc[i, j]
                if not (-0.1 <= value <= 2):
                    invalid_positions.append((i + 2, j + 2, value))  # 위치 조정 (+2)

        # 2. 대각 원소 중 1 이하인 값의 위치와 값 저장
        diagonal_invalid_positions = []
        for i in range(leontief.shape[0]):
            value = leontief.iloc[i, i]
            if value < 1:
                diagonal_invalid_positions.append((i + 2, i + 2, value))  # 위치 조정 (+2)

        # 결과 출력
        if invalid_positions:
            st.write("조건(-0.1 ~ 2.0)에 맞지 않는 위치와 값:")
            for pos in invalid_positions:
                st.write(f"위치: {pos[:2]}, 값: {pos[2]}")
        else:
            st.write("모든 값이 -0.1 ~ 2 사이의 조건을 만족합니다.")

        # 대각 원소 조건 확인 및 결과 출력
        if diagonal_invalid_positions:
            st.write("대각 원소 중 1 미만인 값이 있습니다:")
            for pos in diagonal_invalid_positions:
                st.write(f"위치: {pos[:2]}, 값: {pos[2]}")
        else:
            st.write("모든 대각 원소가 1보다 큽니다.")



        with st.sidebar.expander('Leontief 과정 matrices'):
            leontief_files = {
            "normalization_denominator": st.session_state['normalization_denominator'],
            "투입계수행렬": st.session_state['df_normalized_with_label'],
            "leontief inverse": st.session_state['df_for_leontief_with_label'],
            "FL-BL": st.session_state['fl_bl'],
            "GDP": st.session_state['gdp_by_industry'],
            "부가가치유발효과": st.session_state['va_multiplier_by_sector'],
            "부가가치계수행렬": st.session_state['df_for_r_with_label'],
            "부가가치계벡터": st.session_state['added_value_denominator']
            }
            download_multiple_csvs_as_zip(leontief_files, zip_name="Leontief 과정 전체(zip)")
            donwload_data(st.session_state['normalization_denominator'], 'normailization denominator')
            donwload_data(st.session_state['df_normalized_with_label'], '투입계수행렬')
            donwload_data(st.session_state['df_for_leontief_with_label'], 'leontief inverse')
            donwload_data(st.session_state['fl_bl'], 'FL-BL')
            donwload_data(st.session_state['gdp_by_industry'], 'GDP')
            donwload_data(st.session_state['va_multiplier_by_sector'], '부가가치유발효과')
            donwload_data(st.session_state['df_for_r_with_label'], '부가가치계수행렬')
            donwload_data(st.session_state['added_value_denominator'], '부가가치계벡터')


        st.subheader("FL-BL Plot")

        # -----------------------------
        # 1) ids_values 만들기 + (중복 제거, 순서 유지)
        # -----------------------------
        ids_values = [item for sublist in st.session_state.ids_simbol.values() for item in sublist]

        seen = set()
        ids_unique = []
        for x in ids_values:
            if x not in seen:
                seen.add(x)
                ids_unique.append(x)

        # -----------------------------
        # 2) 토글을 "한 행"에 전부 배치 (각 아이템별 토글)
        #    - 기본값 True (전부 ON)
        # -----------------------------
        if len(ids_unique) > 0:
            cols = st.columns(len(ids_unique))  # ✅ 한 줄에 전부
            selected_ids = []
            for i, name in enumerate(ids_unique):
                # key는 안전하게(특수문자 제거) + i 붙여서 중복 방지
                safe = re.sub(r"[^0-9a-zA-Z가-힣_]", "_", str(name))
                key = f"hl_{i}_{safe}"

                with cols[i]:
                    if st.toggle(str(name), value=True, key=key):
                        selected_ids.append(name)
        else:
            selected_ids = []

        # -----------------------------
        # 3) DF 준비 (첫 행 제거는 통일)
        # -----------------------------
        df = st.session_state['fl_bl'].copy()
        df = df.iloc[1:, :]

        highlight_df = df[df[1].isin(selected_ids)]

        # -----------------------------
        # 4) Plot: 전체는 other 스타일로 그리고,
        #         토글 ON인 애들만 빨간 + 라벨 overlay
        # -----------------------------
        fig, ax = plt.subplots(figsize=(12, 10))

        # 전체 기본 점 (other 스타일)
        ax.scatter(df['2'], df['3'], facecolors='none', edgecolors='black', s=100)

        # 선택된 애들만 강조 + 라벨
        if not highlight_df.empty:
            ax.scatter(highlight_df['2'], highlight_df['3'], color='red', s=150)
            for _, row in highlight_df.iterrows():
                ax.text(row['2'], row['3'], row[1], color='black', fontsize=16, ha='right')

        ax.set_xlabel('FL', fontsize=14)
        ax.set_ylabel('BL', fontsize=14)
        ax.axhline(1, color='black', linestyle='--', linewidth=1)
        ax.axvline(1, color='black', linestyle='--', linewidth=1)

        st.pyplot(fig)


        # 사이드바 expander 에 다운로드 버튼 추가
        with st.sidebar.expander("Plot 다운로드"):
            buf = io.BytesIO()
            # PNG 포맷으로 버퍼에 저장
            fig.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            st.download_button(
                label="Plot 이미지 다운로드",
                data=buf,
                file_name="fl_bl_plot.png",
                mime="image/png"
            )

        win_A = st.session_state['df_normalized_with_label'].iloc[2:, 2:].copy().values
        win_epsilon = 0.05

        win_N0 = compute_leontief_inverse(win_A, epsilon=win_epsilon)

        win_Diagon, win_N = separate_diagonals(win_N0)

        win_s = np.sum(win_N)
        win_ss = np.sum(np.square(win_N))
        win_n = win_A.shape[0]
        win_num_elements = win_n**2 - win_n
        win_avg = win_s / win_num_elements
        win_variance = win_ss / win_num_elements - win_avg**2
        if win_variance < 0:
            win_variance = 0
        win_stdev = np.sqrt(win_variance)

        win_delta = win_avg - win_stdev


        win_N0_label = st.session_state['df_normalized_with_label'].copy()
        win_N0_label.iloc[2:,2:]= win_N0
        
        st.subheader("1. 네트워크 기본 행렬 (Delta 적용을 위한 행렬)")
        win_N_label = st.session_state['df_normalized_with_label'].copy()
        win_N_label.iloc[2:,2:]= win_N
        st.write(win_N_label)

        st.write(f"\noff-diagonal 원소의 평균: {win_avg}")
        st.write(f"off-diagonal 원소의 표준편차: {win_stdev}")
        st.write(f"임계치 (delta): {win_delta}")

        win_col1, win_col2= st.columns(2)
        with win_col1:
            win_delta_userinput = float(st.text_input('delta를 입력하세요','0.000'))
        with win_col2:
            if st.button('Apply delta'):
                st.session_state.delta = win_delta_userinput


        if 'delta' in st.session_state:
            try:
                N_final = threshold_network(win_N, st.session_state.delta)
                win_N_final_label = st.session_state['df_normalized_with_label'].copy()
                win_N_final_label.iloc[2:,2:]= N_final

                N = N_final.shape[0]  # 행렬의 크기 (정방행렬 기준)
                total_possible_links = N**2 - N  # 대각선 제외한 전체 가능한 링크 수
                survived_links = np.count_nonzero(N_final)  # 0이 아닌 값 개수 (살아남은 링크 수)
                link_ratio = survived_links / total_possible_links  # 비율

                st.write(f"적용된 delta: {st.session_state.delta} / N:{N}")
                st.write(f"남아 있는 링크 수: {survived_links} / 전체 가능 링크 수: {total_possible_links}")
                st.write(f"남아 있는 링크 비율: {link_ratio:.4f} ({link_ratio * 100:.2f}%)")



                G_n = nx.DiGraph()

                # 모든 노드 가져오기 (고립된 노드 포함)
                all_nodes_n = set(range(N_final.shape[0]))  # BN의 크기 기준으로 전체 노드 설정
                G_n.add_nodes_from(all_nodes_n)  # 모든 노드 추가 (고립 노드 포함)

                rows_n, cols_n = np.where(N_final != 0)
                weights_n = N_final[rows_n, cols_n]
                edges_n = [(j, i, {'weight': w}) for i, j, w in zip(rows_n, cols_n, weights_n)]
                G_n.add_edges_from(edges_n)


                n_df_degree, n_df_bc, n_df_cc, n_df_ev, n_df_hi, n_df_kim, n_gd_in_mean, n_gd_in_std, n_gd_out_mean, n_gd_out_std, n_bc_mean, n_bc_std, n_cc_in_mean, n_cc_in_std, n_cc_out_mean, n_cc_out_std, n_ev_in_mean, n_ev_in_std, n_ev_out_mean, n_ev_out_std, n_hub_mean, n_hub_std, n_ah_mean, n_ah_std, n_const_mean,n_const_std, n_eff_mean, n_eff_std = calculate_network_centralities(G_n, st.session_state['df_normalized_with_label'],True)

                BN = create_binary_network(N_final)
                win_BN_final_label = st.session_state['df_normalized_with_label'].copy()
                win_BN_final_label.iloc[2:,2:]= BN

                G_bn = nx.DiGraph()

                # 모든 노드 가져오기 (고립된 노드 포함)
                all_nodes = set(range(BN.shape[0]))  # BN의 크기 기준으로 전체 노드 설정
                G_bn.add_nodes_from(all_nodes)  # 모든 노드 추가 (고립 노드 포함)

                # 1이 있는 위치를 찾아서 엣지를 추가
                cols_bn, rows_bn = np.where(BN == 1)
                edges_bn = zip(rows_bn, cols_bn)  # (i, j) 형태로 변환

                G_bn.add_edges_from(edges_bn)


                bn_df_degree, bn_df_bc, bn_df_cc, bn_df_ev, bn_df_hi, bn_df_kim, bn_gd_in_mean, bn_gd_in_std, bn_gd_out_mean, bn_gd_out_std, bn_bc_mean, bn_bc_std, bn_cc_in_mean, bn_cc_in_std, bn_cc_out_mean, bn_cc_out_std, bn_ev_in_mean, bn_ev_in_std, bn_ev_out_mean, bn_ev_out_std, bn_hub_mean, bn_hub_std, bn_ah_mean, bn_ah_std, bn_const_mean,bn_const_std, bn_eff_mean, bn_eff_std = calculate_network_centralities(G_bn, st.session_state['df_normalized_with_label'],False)


                UN = create_undirected_network(BN)

                win_UN_final_label = st.session_state['df_normalized_with_label'].copy()
                win_UN_final_label.iloc[2:,2:]= UN

                col1_net, col2_net, col3_net = st.tabs([f"임계치 적용 후 네트워크 행렬", '이진화된 방향성 네트워크 (BN)', '무방향 이진 네트워크 (UN)'])
                with col1_net:
                    st.write(win_N_final_label)
                    st.markdown("##### 임계치 적용 후 네트워크 행렬의 지표")
                    col1_n, col2_n, col3_n, col4_n, col5_n, col6_n = st.tabs([f"Degree Centrality", 'Betweenness Centrality',"Closeness Centrality", "Eigenvector Centrality", "Hub & Authority","constraints&efficiencies"])
                    with col1_n:
                        st.dataframe(n_df_degree)
                        st.write("In-Degree: Mean =", n_gd_in_mean, ", Std =", n_gd_in_std)
                        st.write("Out-Degree: Mean =", n_gd_out_mean, ", Std =", n_gd_out_std)
                    
                    with col2_n:
                        st.dataframe(
                            n_df_bc,
                            column_config={'Betweenness Centrality': st.column_config.NumberColumn('Betweenness Centrality', format='%.12f')}
                        )
                        st.write("Betweenness Centrality: Mean =", n_bc_mean, ", Std =", n_bc_std)
                    
                    with col3_n:
                        st.dataframe(
                            n_df_cc,
                            column_config={
                                'Indegree_Closeness Centrality': st.column_config.NumberColumn('Indegree_Closeness Centrality', format='%.12f'),
                                'Outdegree_Closeness Centrality': st.column_config.NumberColumn('Outdegree_Closeness Centrality', format='%.12f')
                            }
                        )
                        st.write("Indegree Closeness Centrality: Mean =", n_cc_in_mean, ", Std =", n_cc_in_std)
                        st.write("Outdegree Closeness Centrality: Mean =", n_cc_out_mean, ", Std =", n_cc_out_std)
                    
                    with col4_n:
                        st.dataframe(
                            n_df_ev,
                            column_config={
                                'Indegree_Eigenvector Centrality': st.column_config.NumberColumn('Indegree_Eigenvector Centrality', format='%.12f'),
                                'Outdegree_Eigenvector Centrality': st.column_config.NumberColumn('Outdegree_Eigenvector Centrality', format='%.12f')
                            }
                        )
                        st.write("Indegree Eigenvector Centrality: Mean =", n_ev_in_mean, ", Std =", n_ev_in_std)
                        st.write("Outdegree Eigenvector Centrality: Mean =", n_ev_out_mean, ", Std =", n_ev_out_std)
                    
                    with col5_n:
                        st.dataframe(
                            n_df_hi,
                            column_config={
                                'HITS Hubs': st.column_config.NumberColumn('HITS Hubs', format='%.12f'),
                                'HITS Authorities': st.column_config.NumberColumn('HITS Authorities', format='%.12f')
                            }
                        )
                        st.write("HITS Hubs: Mean =", n_hub_mean, ", Std =", n_hub_std)
                        st.write("HITS Authorities: Mean =", n_ah_mean, ", Std =", n_ah_std)
                    with col6_n:
                        st.dataframe(
                            n_df_kim,
                            column_config={
                                'Constraint factor': st.column_config.NumberColumn('Constraint factor', format='%.12f'),
                                'Efficiency factor': st.column_config.NumberColumn('Efficiency factor', format='%.12f')
                            }
                        )
                        st.write("Constraint factor: Mean =", n_const_mean, ", Std =", n_const_std)
                        st.write("Efficiency factor: Mean =", n_eff_mean, ", Std =", n_eff_std)

                with col2_net:
                    st.write(win_BN_final_label)
                     # 1. 노드 이름(A, B, C01, ...) 리스트로 추출
                    # win_BN_final_label 의 2번째 열(인덱스 0)에 실제 노드명이 들어있다고 가정
                    node_names_delta = win_BN_final_label.iloc[2:, 0].tolist()  

                    # 3. 레이아웃 계산
                    pos = nx.spring_layout(G_bn, seed=42)

                    # 4. 시각화
                    fig, ax = plt.subplots(figsize=(8, 6))
                    nx.draw_networkx_nodes(G_bn, pos, node_size=400, ax=ax)
                    nx.draw_networkx_edges(G_bn, pos, arrowstyle='->', arrowsize=10, ax=ax)

                    # 5. 레이블 매핑 (노드 번호 → 실제 이름)
                    label_dict = {i: name for i, name in enumerate(node_names_delta)}

                    # 6. 레이블 그리기
                    nx.draw_networkx_labels(G_bn, pos, labels=label_dict, font_size=10, ax=ax)

                    ax.set_title("Delta-Thresholded Binary Network (DBN)", fontsize=14)
                    ax.axis('off')
                    st.pyplot(fig)




                    st.markdown("##### 이진 방향성 네트워크 행렬의 지표")
                    col1_bn, col2_bn, col3_bn, col4_bn, col5_bn, col6_bn = st.tabs([f"Degree Centrality", 'Betweenness Centrality',"Closeness Centrality", "Eigenvector Centrality", "Hub & Authority", "constraints&efficiencies"])
                    with col1_bn:
                        st.dataframe(bn_df_degree)
                        st.write("In-Degree: Mean =", bn_gd_in_mean, ", Std =", bn_gd_in_std)
                        st.write("Out-Degree: Mean =", bn_gd_out_mean, ", Std =", bn_gd_out_std)
                    
                    with col2_bn:
                        st.dataframe(
                            bn_df_bc,
                            column_config={'Betweenness Centrality': st.column_config.NumberColumn('Betweenness Centrality', format='%.12f')}
                        )
                        st.write("Betweenness Centrality: Mean =", bn_bc_mean, ", Std =", bn_bc_std)
                    
                    with col3_bn:
                        st.dataframe(
                            bn_df_cc,
                            column_config={
                                'Indegree_Closeness Centrality': st.column_config.NumberColumn('Indegree_Closeness Centrality', format='%.12f'),
                                'Outdegree_Closeness Centrality': st.column_config.NumberColumn('Outdegree_Closeness Centrality', format='%.12f')
                            }
                        )
                        st.write("Indegree Closeness Centrality: Mean =", bn_cc_in_mean, ", Std =", bn_cc_in_std)
                        st.write("Outdegree Closeness Centrality: Mean =", bn_cc_out_mean, ", Std =", bn_cc_out_std)
                    
                    with col4_bn:
                        st.dataframe(
                            bn_df_ev,
                            column_config={
                                'Indegree_Eigenvector Centrality': st.column_config.NumberColumn('Indegree_Eigenvector Centrality', format='%.12f'),
                                'Outdegree_Eigenvector Centrality': st.column_config.NumberColumn('Outdegree_Eigenvector Centrality', format='%.12f')
                            }
                        )
                        st.write("Indegree Eigenvector Centrality: Mean =", bn_ev_in_mean, ", Std =", bn_ev_in_std)
                        st.write("Outdegree Eigenvector Centrality: Mean =", bn_ev_out_mean, ", Std =", bn_ev_out_std)
                    
                    with col5_bn:
                        st.dataframe(
                            bn_df_hi,
                            column_config={
                                'HITS Hubs': st.column_config.NumberColumn('HITS Hubs', format='%.12f'),
                                'HITS Authorities': st.column_config.NumberColumn('HITS Authorities', format='%.12f')
                            }
                        )
                        st.write("HITS Hubs: Mean =", bn_hub_mean, ", Std =", bn_hub_std)
                        st.write("HITS Authorities: Mean =", bn_ah_mean, ", Std =", bn_ah_std)

                    with col6_bn:
                        st.dataframe(
                            bn_df_kim,
                            column_config={
                                'Constraint factor': st.column_config.NumberColumn('Constraint factor', format='%.12f'),
                                'Efficiency factor': st.column_config.NumberColumn('Efficiency factor', format='%.12f')
                            }
                        )
                        st.write("Constraint factor: Mean =", bn_const_mean, ", Std =", bn_const_std)
                        st.write("Efficiency factor: Mean =", bn_eff_mean, ", Std =", bn_eff_std)
                with col3_net:
                    st.write(win_UN_final_label)


                with st.sidebar.expander(f"filtered file(delta:{st.session_state.delta})"):
                    delta_original = {
                    "delta_original_degree_centrality": n_df_degree,
                    "delta_original_betweenness_centrality": n_df_bc,
                    "delta_original_closeness_centrality": n_df_cc,
                    "delta_original_eigenvector_centrality": n_df_ev,
                    "delta_original_hits": n_df_hi
                                            }
                    delta_bn = {
                    "delta_bn_degree_centrality": bn_df_degree,
                    "delta_bn_betweenness_centrality": bn_df_bc,
                    "delta_bn_closeness_centrality": bn_df_cc,
                    "delta_bn_eigenvector_centrality": bn_df_ev,
                    "delta_bn_hits": bn_df_hi
                                            }
                    
                    all_delta = {
                    "filtered_matrix_X(delta)":          win_N_final_label,
                    **delta_original,
                    "binary_matrix(delta)":              win_BN_final_label,
                    **delta_bn,
                    "undirected_binary_matrix(delta)":   win_UN_final_label
                    }

                    download_multiple_csvs_as_zip(
                        all_delta,
                        zip_name="delta 적용 전체 결과들(zip)"
                    )
                    donwload_data(win_N_final_label, 'filtered_matrix_X(delta)')
                    download_multiple_csvs_as_zip(delta_original, zip_name="delta 적용 네트워크의 지표들(zip)")
                    donwload_data(win_BN_final_label, 'binary_matrix(delta)')
                    download_multiple_csvs_as_zip(delta_bn, zip_name="delta 적용 BN 네트워크의 지표들(zip)")
                    donwload_data(win_UN_final_label, 'undirected_binary_matrix(delta)')
                    

            except:
                st.write("Delta 값이 너무 큽니다. 값을 줄여주세요.")




        st.header("2. 아래는 임계값을 기준으로 filtering 결과")
        st.subheader('threshold에 따른 생존비율 그래프')
        extract_network_method_b(st.session_state['df_for_leontief_with_label'].iloc[2:, 2:])
        col1, col2= st.columns(2)
        with col1:
            threshold = float(st.text_input('threshold를 입력하세요','0.000'))
        with col2:
            if st.button('Apply threshold'):
                st.session_state.threshold = threshold
                st.session_state.threshold_cal = True


    if 'threshold' in st.session_state and st.session_state.show_edited:
        if st.session_state.threshold_cal:
            # binary matrix 생성
            binary_matrix = make_binary_matrix(st.session_state['df_for_leontief_with_label'].iloc[2:, 2:].apply(pd.to_numeric, errors='coerce'), st.session_state.threshold)
            _, binary_matrix = separate_diagonals(binary_matrix)
            binary_matrix_with_label = st.session_state['df_for_leontief'].copy()
            binary_matrix_with_label.iloc[2:,2:] = binary_matrix


            filtered_matrix_X = st.session_state['df_for_leontief'].copy()
            filtered_matrix_X.iloc[2:, 2:] = filtered_matrix_X.iloc[2:, 2:].apply(pd.to_numeric, errors='coerce')*binary_matrix

            filtered_normalized = st.session_state['df_normalized_with_label']
            filtered_normalized.iloc[2:, 2:] = st.session_state['df_normalized_with_label'].iloc[2:, 2:].apply(pd.to_numeric, errors='coerce')*binary_matrix

            filtered_leontief = st.session_state['df_for_leontief_with_label']
            filtered_leontief.iloc[2:, 2:] = st.session_state['df_for_leontief_with_label'].iloc[2:, 2:].apply(pd.to_numeric, errors='coerce')*binary_matrix

            G_tn = nx.DiGraph()

            # 모든 노드 가져오기 (고립된 노드 포함)
            all_nodes_tn = set(range(filtered_leontief.iloc[2:, 2:].shape[0]))
            G_tn.add_nodes_from(all_nodes_tn)  # 모든 노드 추가 (고립 노드 포함)

            rows_tn, cols_tn = np.where(filtered_leontief.iloc[2:, 2:] != 0)
            weights_tn = filtered_leontief.iloc[2:, 2:].to_numpy()[rows_tn, cols_tn]
            edges_tn = [(j, i, {'weight': w}) for i, j, w in zip(rows_tn, cols_tn, weights_tn)]
            G_tn.add_edges_from(edges_tn)


            tn_df_degree, tn_df_bc, tn_df_cc, tn_df_ev, tn_df_hi,tn_df_kim, tn_gd_in_mean, tn_gd_in_std, tn_gd_out_mean, tn_gd_out_std, tn_bc_mean, tn_bc_std, tn_cc_in_mean, tn_cc_in_std, tn_cc_out_mean, tn_cc_out_std, tn_ev_in_mean, tn_ev_in_std, tn_ev_out_mean, tn_ev_out_std, tn_hub_mean, tn_hub_std, tn_ah_mean, tn_ah_std, tn_const_mean,tn_const_std, tn_eff_mean, tn_eff_std = calculate_network_centralities(G_tn, st.session_state['df_normalized_with_label'],True)
            
            tbn_df_degree, tbn_df_bc, tbn_df_cc, tbn_df_ev, tbn_df_hi,tbn_df_kim, tbn_gd_in_mean, tbn_gd_in_std, tbn_gd_out_mean, tbn_gd_out_std, tbn_bc_mean, tbn_bc_std, tbn_cc_in_mean, tbn_cc_in_std, tbn_cc_out_mean, tbn_cc_out_std, tbn_ev_in_mean, tbn_ev_in_std, tbn_ev_out_mean, tbn_ev_out_std, tbn_hub_mean, tbn_hub_std, tbn_ah_mean, tbn_ah_std, tbn_const_mean, tbn_const_std, tbn_eff_mean, tbn_eff_std = calculate_network_centralities(G_tn, st.session_state['df_normalized_with_label'],False)

        st.subheader('Threshold 적용 후 Filtered matrices')

        col1, col2, col3, col4 = st.tabs(['Filtered_leontief', 'Binary_matrix','Filtered_matrix','Filtered_Normalized'])
        with col1:
            st.write(filtered_leontief)
            st.markdown("##### Threshold 적용 후 네트워크 행렬의 지표")
            col1_tn, col2_tn, col3_tn, col4_tn, col5_tn, col6_tn = st.tabs([f"Degree Centrality", 'Betweenness Centrality',"Closeness Centrality", "Eigenvector Centrality", "Hub & Authority", 'constraints&efficiencies'])
            with col1_tn:
                st.dataframe(tn_df_degree)
                st.write("In-Degree: Mean =", tn_gd_in_mean, ", Std =", tn_gd_in_std)
                st.write("Out-Degree: Mean =", tn_gd_out_mean, ", Std =", tn_gd_out_std)
            
            with col2_tn:
                st.dataframe(
                    tn_df_bc,
                    column_config={'Betweenness Centrality': st.column_config.NumberColumn('Betweenness Centrality', format='%.12f')}
                )
                st.write("Betweenness Centrality: Mean =", tn_bc_mean, ", Std =", tn_bc_std)
            
            with col3_tn:
                st.dataframe(
                    tn_df_cc,
                    column_config={
                        'Indegree_Closeness Centrality': st.column_config.NumberColumn('Indegree_Closeness Centrality', format='%.12f'),
                        'Outdegree_Closeness Centrality': st.column_config.NumberColumn('Outdegree_Closeness Centrality', format='%.12f')
                    }
                )
                st.write("Indegree Closeness Centrality: Mean =", tn_cc_in_mean, ", Std =", tn_cc_in_std)
                st.write("Outdegree Closeness Centrality: Mean =", tn_cc_out_mean, ", Std =", tn_cc_out_std)
            
            with col4_tn:
                st.dataframe(
                    tn_df_ev,
                    column_config={
                        'Indegree_Eigenvector Centrality': st.column_config.NumberColumn('Indegree_Eigenvector Centrality', format='%.12f'),
                        'Outdegree_Eigenvector Centrality': st.column_config.NumberColumn('Outdegree_Eigenvector Centrality', format='%.12f')
                    }
                )
                st.write("Indegree Eigenvector Centrality: Mean =", tn_ev_in_mean, ", Std =", tn_ev_in_std)
                st.write("Outdegree Eigenvector Centrality: Mean =", tn_ev_out_mean, ", Std =", tn_ev_out_std)
            
            with col5_tn:
                st.dataframe(
                    tn_df_hi,
                    column_config={
                        'HITS Hubs': st.column_config.NumberColumn('HITS Hubs', format='%.12f'),
                        'HITS Authorities': st.column_config.NumberColumn('HITS Authorities', format='%.12f')
                    }
                )
                st.write("HITS Hubs: Mean =", tn_hub_mean, ", Std =", tn_hub_std)
                st.write("HITS Authorities: Mean =", tn_ah_mean, ", Std =", tn_ah_std)

            with col6_tn:
                st.dataframe(
                    tn_df_kim,
                    column_config={
                        'Constraint factor': st.column_config.NumberColumn('Constraint factor', format='%.12f'),
                        'Efficiency factor': st.column_config.NumberColumn('Efficiency factor', format='%.12f')
                    }
                )
                st.write("Constraint factor: Mean =", tn_const_mean, ", Std =", tn_const_std)
                st.write("Efficiency factor: Mean =", tn_eff_mean, ", Std =", tn_eff_std)

        with col2:
            st.write(binary_matrix_with_label)
            # 1. 노드 이름(A, B, C01, ...) 리스트로 추출
            #    binary_matrix_with_label 의 2번째 행부터 첫 번째 열(0번) 값을 가져옵니다.
            node_names_tn = binary_matrix_with_label.iloc[2:, 0].tolist()

            # 2. 레이아웃 계산
            pos_tn = nx.spring_layout(G_tn, seed=42)

            # 3. 시각화
            fig_tn, ax_tn = plt.subplots(figsize=(8, 6))
            nx.draw_networkx_nodes(G_tn, pos_tn, node_size=400, ax=ax_tn)
            nx.draw_networkx_edges(G_tn, pos_tn, arrowstyle='->', arrowsize=10, ax=ax_tn)

            # 4. 레이블 매핑 (노드 번호 → 실제 이름)
            label_dict_tn = {i: name for i, name in enumerate(node_names_tn)}

            # 5. 레이블 그리기
            nx.draw_networkx_labels(G_tn, pos_tn, labels=label_dict_tn, font_size=10, ax=ax_tn)

            ax_tn.set_title("Thresholded Binary Network (TBN)", fontsize=14)
            ax_tn.axis('off')
            st.pyplot(fig_tn)

            st.markdown("##### 이진 방향성 네트워크 행렬의 지표")
            col1_tbn, col2_tbn, col3_tbn, col4_tbn, col5_tbn, col6_tbn = st.tabs([f"Degree Centrality", 'Betweenness Centrality',"Closeness Centrality", "Eigenvector Centrality", "Hub & Authority", "constraints&efficiencies"])
            with col1_tbn:
                st.dataframe(tbn_df_degree)
                st.write("In-Degree: Mean =", tbn_gd_in_mean, ", Std =", tbn_gd_in_std)
                st.write("Out-Degree: Mean =", tbn_gd_out_mean, ", Std =", tbn_gd_out_std)
            
            with col2_tbn:
                st.dataframe(
                    tbn_df_bc,
                    column_config={'Betweenness Centrality': st.column_config.NumberColumn('Betweenness Centrality', format='%.12f')}
                )
                st.write("Betweenness Centrality: Mean =", tbn_bc_mean, ", Std =", tbn_bc_std)
            
            with col3_tbn:
                st.dataframe(
                    tbn_df_cc,
                    column_config={
                        'Indegree_Closeness Centrality': st.column_config.NumberColumn('Indegree_Closeness Centrality', format='%.12f'),
                        'Outdegree_Closeness Centrality': st.column_config.NumberColumn('Outdegree_Closeness Centrality', format='%.12f')
                    }
                )
                st.write("Indegree Closeness Centrality: Mean =", tbn_cc_in_mean, ", Std =", tbn_cc_in_std)
                st.write("Outdegree Closeness Centrality: Mean =", tbn_cc_out_mean, ", Std =", tbn_cc_out_std)
            
            with col4_tbn:
                st.dataframe(
                    tbn_df_ev,
                    column_config={
                        'Indegree_Eigenvector Centrality': st.column_config.NumberColumn('Indegree_Eigenvector Centrality', format='%.12f'),
                        'Outdegree_Eigenvector Centrality': st.column_config.NumberColumn('Outdegree_Eigenvector Centrality', format='%.12f')
                    }
                )
                st.write("Indegree Eigenvector Centrality: Mean =", tbn_ev_in_mean, ", Std =", tbn_ev_in_std)
                st.write("Outdegree Eigenvector Centrality: Mean =", tbn_ev_out_mean, ", Std =", tbn_ev_out_std)
            
            with col5_tbn:
                st.dataframe(
                    tbn_df_hi,
                    column_config={
                        'HITS Hubs': st.column_config.NumberColumn('HITS Hubs', format='%.12f'),
                        'HITS Authorities': st.column_config.NumberColumn('HITS Authorities', format='%.12f')
                    }
                )
                st.write("HITS Hubs: Mean =", tbn_hub_mean, ", Std =", tbn_hub_std)
                st.write("HITS Authorities: Mean =", tbn_ah_mean, ", Std =", tbn_ah_std)

            with col6_tbn:
                st.dataframe(
                    tbn_df_kim,
                    column_config={
                        'Constraint factor': st.column_config.NumberColumn('Constraint factor', format='%.12f'),
                        'Efficiency factor': st.column_config.NumberColumn('Efficiency factor', format='%.12f')
                    }
                )
                st.write("Constraint factor: Mean =", tbn_const_mean, ", Std =", tbn_const_std)
                st.write("Efficiency factor: Mean =", tbn_eff_mean, ", Std =", tbn_eff_std)
        with col3:
            st.write(filtered_matrix_X)
        with col4:
            st.write(filtered_normalized)


        with st.sidebar.expander(f"filtered file(threshold:{st.session_state.threshold})"):
            threshold_original = {
            "threshold_original_degree_centrality": tn_df_degree,
            "threshold_original_betweenness_centrality": tn_df_bc,
            "threshold_original_closeness_centrality": tn_df_cc,
            "threshold_original_eigenvector_centrality": tn_df_ev,
            "threshold_original_hits": tn_df_hi
                                    }
            threshold_bn = {
            "threshold_bn_degree_centrality": tbn_df_degree,
            "threshold_bn_betweenness_centrality": tbn_df_bc,
            "threshold_bn_closeness_centrality": tbn_df_cc,
            "threshold_bn_eigenvector_centrality": tbn_df_ev,
            "threshold_bn_hits": tbn_df_hi
                                    }
            
            # 모든 결과를 한 dict으로 합치기
            all_threshold = {
                "filtered_leontief(threshold)":        filtered_leontief,
                **threshold_original,
                "binary_matrix(threshold)":            binary_matrix_with_label,
                **threshold_bn,
                "filtered_matrix_X(threshold)":        filtered_matrix_X,
                "filtered_normalized(threshold)":      filtered_normalized
            }
            # ZIP으로 한 번에 다운로드
            download_multiple_csvs_as_zip(
                all_threshold,
                zip_name="threshold 적용 전체 결과들(zip)"
            )
            donwload_data(filtered_leontief, 'filtered_leontief(threshold)')
            download_multiple_csvs_as_zip(threshold_original, zip_name="threshold 적용 네트워크의 지표들(zip)")
            donwload_data(binary_matrix_with_label, 'binary_matrix(threshold)')
            download_multiple_csvs_as_zip(threshold_bn, zip_name="threshold 적용 BN 네트워크의 지표들(zip)")
            donwload_data(filtered_matrix_X, 'filtered_matrix_X(threshold)')
            donwload_data(filtered_normalized, 'filtered_normalized(threshold)')

    
            # [공통] 필요한 곳에 한 번만 넣어 두세요
    def _gather_all_dataframes() -> dict[str, pd.DataFrame]:
        """session_state 안에 존재하는 모든 DataFrame을 한 ZIP으로 묶을 dict 생성"""
        dfs: dict[str, pd.DataFrame] = {}

        # 1) 최초 업로드 원본
        if 'df' in st.session_state:
            dfs['uploaded_df']          = st.session_state['df']
            if 'mid_ID_idx' in st.session_state:
                dfs['uploaded_matrix_X'] = get_submatrix_withlabel(
                    st.session_state['df'], first_idx[0], first_idx[1],
                    st.session_state['mid_ID_idx'][0], st.session_state['mid_ID_idx'][1],
                    first_idx, numberoflabel=number_of_label)
                dfs['uploaded_matrix_R'] = get_submatrix_withlabel(
                    st.session_state['df'], st.session_state['mid_ID_idx'][0]+1, first_idx[1],
                    st.session_state['df'].shape[0]-1, st.session_state['mid_ID_idx'][1],
                    first_idx, numberoflabel=number_of_label)
                dfs['uploaded_matrix_C'] = get_submatrix_withlabel(
                    st.session_state['df'], first_idx[0], st.session_state['mid_ID_idx'][1]+1,
                    st.session_state['mid_ID_idx'][0], st.session_state['df'].shape[1]-1,
                    first_idx, numberoflabel=number_of_label)

        # 2) 편집 완료본
        if 'df_edited' in st.session_state and 'edited_matrix_X' in locals():
            dfs['edited_df']           = st.session_state['df_edited']
            dfs['edited_matrix_X']     = edited_matrix_X
            dfs['edited_matrix_R']     = edited_matrix_R
            dfs['edited_matrix_C']     = edited_matrix_C

        # 3) Leontief 관련
        if 'df_for_leontief_with_label' in st.session_state:
            dfs['투입계수행렬']             = st.session_state['df_normalized_with_label']
            dfs['leontief_inverse']        = st.session_state['df_for_leontief_with_label']
            dfs['FL_BL']                   = st.session_state['fl_bl']
            dfs['부가가치계수행렬']          = st.session_state['df_for_r_with_label']
            dfs['부가가치계벡터']            = st.session_state['added_value_denominator']
            dfs['normalization_denominator'] = st.session_state['normalization_denominator']

        # 4) delta 필터 결과
        if 'delta' in st.session_state and 'win_N_final_label' in locals(): 
            dfs['filtered_matrix_X(delta)']      = win_N_final_label
            dfs['binary_matrix(delta)']          = win_BN_final_label
            dfs['undirected_binary_matrix(delta)'] = win_UN_final_label
            dfs.update({                         # 지표들
                'delta_original_degree_centrality':      n_df_degree,
                'delta_original_betweenness_centrality': n_df_bc,
                'delta_original_closeness_centrality':   n_df_cc,
                'delta_original_eigenvector_centrality': n_df_ev,
                'delta_original_hits':                  n_df_hi,
                'delta_bn_degree_centrality':           bn_df_degree,
                'delta_bn_betweenness_centrality':      bn_df_bc,
                'delta_bn_closeness_centrality':        bn_df_cc,
                'delta_bn_eigenvector_centrality':      bn_df_ev,
                'delta_bn_hits':                        bn_df_hi,
            })

        # 5) threshold 필터 결과
        if 'threshold' in st.session_state and 'binary_matrix_with_label' in locals():
            dfs['filtered_leontief(threshold)']   = filtered_leontief
            dfs['binary_matrix(threshold)']       = binary_matrix_with_label
            dfs['filtered_matrix_X(threshold)']   = filtered_matrix_X
            dfs['filtered_normalized(threshold)'] = filtered_normalized
            dfs.update({
                'threshold_original_degree_centrality':      tn_df_degree,
                'threshold_original_betweenness_centrality': tn_df_bc,
                'threshold_original_closeness_centrality':   tn_df_cc,
                'threshold_original_eigenvector_centrality': tn_df_ev,
                'threshold_original_hits':                  tn_df_hi,
                'threshold_bn_degree_centrality':           tbn_df_degree,
                'threshold_bn_betweenness_centrality':      tbn_df_bc,
                'threshold_bn_closeness_centrality':        tbn_df_cc,
                'threshold_bn_eigenvector_centrality':      tbn_df_ev,
                'threshold_bn_hits':                        tbn_df_hi,
            })

        return dfs
    with st.sidebar.expander("전체 결과 ZIP 다운로드"):
        all_dfs = _gather_all_dataframes()
        if all_dfs:
            download_multiple_csvs_as_zip(all_dfs, zip_name="IO_analysis_all_results(zip)")

        else:
            st.write("아직 저장된 결과가 없습니다. 먼저 분석을 실행하세요.")
    st.sidebar.header('수정내역')
    with st.sidebar.expander('수정내역 보기'):
        st.text(st.session_state['data_editing_log'])

if __name__ == "__main__":
    main()
