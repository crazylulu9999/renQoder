# MSIX Packaging Guide for renQoder

Microsoft Store 제출을 위한 MSIX 패키징 가이드입니다.

## 📋 사전 준비

### 1. MSIX Packaging Tool 설치
```cmd
winget install "MSIX Packaging Tool"
```
또는 Microsoft Store에서 직접 설치

### 2. 필요한 파일 확인
- ✅ `dist\renQoder-v0.4.0.exe` (빌드된 실행 파일)
- ✅ `src\renqoder\resources\icon.ico` (앱 아이콘)
- ✅ `README.md` (앱 설명)

---

## 🔧 MSIX Packaging Tool 사용법

### Step 1: MSIX Packaging Tool 실행

1. **MSIX Packaging Tool**을 관리자 권한으로 실행합니다.
2. 메인 화면에서 **"Application package"** 선택
3. **"Create package on this computer"** 선택

### Step 2: 패키징 환경 준비

**Prepare computer** 화면에서:
- ✅ **MSIX Packaging Tool Driver** 설치 확인
- ✅ 백그라운드 프로세스 최소화 (권장)
- **Next** 클릭

### Step 3: 설치 프로그램 선택

**Select installer** 화면에서:

1. **Browse** 클릭하여 `dist\renQoder-v0.4.0.exe` 선택
2. **Signing preference**: 
   - 테스트용: "Sign with Device Guard signing" 또는 임시 인증서
   - 실제 배포용: 나중에 Partner Center에서 자동 서명됨
3. **Package information**:
   - **Package name**: `renQoder`
   - **Package display name**: `renQoder - Video Encoder`
   - **Publisher name**: `CN=YourName` (Partner Center에서 받은 Publisher ID 사용)
   - **Publisher display name**: 본인 이름 또는 회사명
   - **Version**: `0.4.0.0` (4자리 형식, 마지막은 반드시 0)
4. **Next** 클릭

### Step 4: 설치 과정 모니터링

**Installation** 화면에서:

1. **자동으로 설치 프로세스가 시작됩니다**
   - renQoder.exe가 실행되면 **한 번 실행해보고 종료**합니다
   - 이 과정에서 앱이 생성하는 파일/레지스트리를 캡처합니다

2. **설치 완료 후**:
   - ✅ "I'm finished installing" 체크
   - **Next** 클릭

### Step 5: 서비스 및 작업 설정

**Services report** 화면:
- renQoder는 서비스를 사용하지 않으므로 **Next** 클릭

### Step 6: 첫 실행 작업

**First launch tasks** 화면:
- 필요시 앱을 한 번 더 실행하여 초기 설정 캡처
- 완료 후 **Next** 클릭

### Step 7: 패키지 정보 확인

**Create package** 화면에서:

1. **Package information** 탭:
   - 모든 정보 재확인
   - **Package editor** 클릭하여 상세 설정

2. **Package editor**에서 중요 설정:
   
   **Capabilities (기능 권한)**:
   - ✅ `runFullTrust` (필수 - Win32 앱이므로)
   - 필요시 추가: `videosLibrary`, `documentsLibrary`

   **Visual Assets (아이콘)**:
   - Square 150x150 Logo: `icon.ico` 사용
   - Square 44x44 Logo: `icon.ico` 사용
   - Store Logo: `icon.ico` 사용
   - Wide 310x150 Logo: 선택사항
   - Splash Screen: 선택사항

   **Application (실행 파일 설정)**:
   - Entry Point: `renQoder-v0.4.0.exe`
   - Display Name: `renQoder`
   - Description: "FFmpeg 기반 비디오 인코더"

3. **저장 후 닫기**

### Step 8: 패키지 생성

1. **Save location** 선택 (예: `c:\dev\renQoder\dist\msix\`)
2. **Create** 클릭
3. 패키징 완료 대기

### Step 9: 패키지 검증

생성된 `.msix` 파일을 테스트:

```cmd
# MSIX 패키지 설치 테스트
Add-AppxPackage -Path "c:\dev\renQoder\dist\msix\renQoder_0.4.0.0_x64.msix"

# 설치된 앱 확인
Get-AppxPackage | Where-Object {$_.Name -like "*renQoder*"}

# 제거 (테스트 후)
Remove-AppxPackage -Package "renQoder_0.3.0.0_x64__xxxxxxxxxx"
```

---

## 🏪 Microsoft Store 제출 준비

### 1. Partner Center 계정 생성
- https://partner.microsoft.com/dashboard 접속
- 개발자 계정 등록 (일회성 비용: 약 $19)

### 2. 앱 예약
1. Partner Center에서 **"New product"** → **"App"** 선택
2. 앱 이름 예약: `renQoder`
3. Publisher ID 확인 (MSIX 재패키징 시 필요)

### 3. MSIX 재패키징 (Publisher ID 적용)
- Partner Center에서 받은 정확한 Publisher ID로 다시 패키징
- 예: `CN=12345678-1234-1234-1234-123456789ABC`

### 4. 제출 정보 준비
- ✅ 앱 설명 (한국어/영어)
- ✅ 스크린샷 (최소 1개, 권장 4-5개)
- ✅ 개인정보 처리방침 URL (필수)
- ✅ 연령 등급 설정
- ✅ 카테고리: "Photo & Video" 또는 "Developer tools"

### 5. MSIX 업로드 및 제출
1. Partner Center에서 **"Start your submission"**
2. **Packages** 섹션에서 `.msix` 파일 업로드
3. 자동 검증 통과 확인
4. 모든 정보 입력 후 **Submit for certification**

---

## 🔍 문제 해결

### MSIX 설치 시 "Publisher 신뢰할 수 없음" 오류
- 테스트 환경에서는 정상 (개발자 모드 활성화 필요)
- Store 배포 시에는 Microsoft가 자동으로 서명하므로 문제 없음

### FFmpeg 의존성 처리
renQoder는 외부 FFmpeg가 필요하므로:
1. **옵션 1**: 앱 설명에 "FFmpeg 별도 설치 필요" 명시
2. **옵션 2**: FFmpeg.exe를 MSIX에 포함 (라이선스 확인 필요)
3. **옵션 3**: 첫 실행 시 자동 다운로드 기능 추가

### 버전 번호 형식
- ✅ 올바른 형식: `0.4.0.0`, `1.0.0.0`
- ❌ 잘못된 형식: `0.3.0`, `v0.3.0`
- Store 제출 시 마지막 자리는 **반드시 0**

---

## 📚 참고 자료

- [MSIX Packaging Tool 공식 문서](https://learn.microsoft.com/windows/msix/packaging-tool/tool-overview)
- [Microsoft Store 제출 가이드](https://learn.microsoft.com/windows/apps/publish/)
- [Partner Center](https://partner.microsoft.com/dashboard)

---

## ✅ 체크리스트

제출 전 확인사항:
- [ ] MSIX 패키지 생성 완료
- [ ] 로컬에서 설치 테스트 완료
- [ ] Partner Center 계정 생성
- [ ] 앱 이름 예약
- [ ] Publisher ID로 재패키징
- [ ] 스크린샷 준비 (PNG, 1366x768 이상)
- [ ] 앱 설명 작성 (한국어/영어)
- [ ] 개인정보 처리방침 준비
- [ ] 연령 등급 설정
- [ ] MSIX 업로드 및 제출
