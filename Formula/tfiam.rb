class Tfiam < Formula
  desc "TFIAM - Analyze Terraform repositories and generate IAM permission recommendations with AI explanations"
  homepage "https://github.com/onoureldin14/tfiam"
  url "https://github.com/onoureldin14/tfiam/archive/refs/heads/main.zip"
  version "1.0.0"
  sha256 "ca75c849eb62f065b596a7bd12efb1cf6d346b89ed21537877a46292fa19f7d3"
  license "MIT"

  depends_on "python@3.11"

  def install
    # Install the package with dependencies
    system "python3.11", "-m", "pip", "install", ".", "--prefix=#{prefix}"

    # The entry point should be automatically created by setuptools
    # But let's ensure it exists
    bin.install_symlink libexec/"bin/tfiam"
  end

  test do
    system "#{bin}/tfiam", "--help"
  end
end
